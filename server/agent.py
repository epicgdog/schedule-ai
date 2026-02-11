from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from sqlalchemy import create_engine, MetaData, select
from modules import get_major_ge_exceptions
import logging
from dotenv import load_dotenv
import os
import json

load_dotenv()

# GE_REQUIRED = ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C1/C2", "D", "E", "F"]

# Unit requirements per GE area (from SJSU GE Unit Overview)
# Area 1 (A): English Communication & Critical Thinking — 9 units total
#   A1 (1C Oral Communication) — 3 units
#   A2 (1A Written Communication) — 3 units
#   A3 (1B Critical Thinking) — 3 units
# Area 2 (B4): Math/Quantitative Reasoning — 3 units
# Area 3 (C): Arts & Humanities — 6 units total
#   C1 (3A Arts) — 3 units
#   C2 (3B Humanities) — 3 units
# Area 4 (D): Social & Behavioral Sciences — 6 units (2 courses)
# Area 5 (B): Physical & Biological Sciences — 7 units total
#   B1 (5A Physical Science) — 3 units
#   B2 (5B Life Science) — 3 units
#   B3 (5C Laboratory) — 1 unit
# Area 6 (F): Ethnic Studies — 3 units
GE_UNITS_REQUIRED = {
    "A1": 3,
    "A2": 3,
    "A3": 3,
    "B1": 3,
    "B2": 3,
    "B3": 1,
    "B4": 3,
    "C1": 3,
    "C2": 3,
    "D": 6,   # 2 courses needed
    "E": 3,
    "F": 3,
}

# Default units per course (most are 3, B3 lab is 1)
DEFAULT_COURSE_UNITS = {
    "B3": 1,
}

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ── SQLAlchemy setup ─────────────────────────────────────────────
# Create engine and reflect tables once at module level
DATABASE = os.getenv("DATABASE")
engine = create_engine(f"sqlite:///{DATABASE}")
metadata = MetaData()
metadata.reflect(bind=engine)

# Table references
ge_courses_table = metadata.tables["ge_courses"]
ap_table = metadata.tables["ap_articulation"]

# Initialize LLM
llm = ChatOpenAI(
    model="gemma3:12b",
    temperature=0.1,
    base_url=os.getenv("LOCAL_IP_KEY"),
    api_key="ollama",
    timeout=120,
)

extract_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a transcript parser. Extract the major and list of classes taken from the transcript.",
        ),
        (
            "user",
            """Parse the following transcript and extract:
1. The student's major (as listed in the transcript)
2. A list of all college classes the student has taken and passed (use course codes like "CS 46A", "MATH 30")
3. A list of any AP (Advanced Placement) exam credits that appear on the transcript
    -If the AP Exam says "subscore" after don not include the word "subscore" in the output

Transcript:
{transcript}

Return ONLY a JSON object in this exact format:
{{
    "major": "extracted major name",
    "classes_taken": ["ENGL 1A", "MATH 30", ...],
    "ap_credits": ["AP English Language and Composition", "AP Calculus AB", ...]
}}

IMPORTANT:
- Put actual college courses in "classes_taken" using their course codes
- Put AP exam credits in "ap_credits" using their full AP exam name
- AP credits often appear as "AP" or "Advanced Placement" or as test credit on transcripts
- If no AP credits are found, return an empty list for "ap_credits"
- Be thorough and extract ALL classes and AP credits mentioned.""",
        ),
    ]
)


GE_REQUIRED = ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C1/C2", "D", "E", "F"]


def get_ge_areas_still_needed(course_categorization: dict) -> tuple:
    """
    Find which GE areas are still needed based on courses taken,
    tracking units earned vs required per area.
    
    Args:
        course_categorization: Result from get_ge_areas_for_courses
        
    Returns:
        Tuple of (still_needed_list, ge_progress_dict)
        - still_needed_list: List of GE area codes not fully satisfied
        - ge_progress_dict: Dict of area -> {"earned": int, "required": int, "courses": list}
    """
    # Build progress tracking per area
    ge_progress = {}
    for area, required in GE_UNITS_REQUIRED.items():
        ge_progress[area] = {
            "earned": 0,
            "required": required,
            "courses": []
        }
    
    # Count units earned per area from taken GE classes
    for course in course_categorization["GE_Classes"]:
        area = course["area"]
        if area in ge_progress:
            units = DEFAULT_COURSE_UNITS.get(area, 3)
            ge_progress[area]["earned"] += units
            ge_progress[area]["courses"].append(course["name"])
    
    # Determine which areas are still needed
    still_needed = []
    
    for required in GE_REQUIRED:
        if required == "C1/C2":
            # Special case: need an additional C course beyond C1 and C2
            c1_courses = len(ge_progress.get("C1", {}).get("courses", []))
            c2_courses = len(ge_progress.get("C2", {}).get("courses", []))
            total_c = c1_courses + c2_courses
            if total_c < 3:
                still_needed.append(required)
        elif required in ge_progress:
            if ge_progress[required]["earned"] < ge_progress[required]["required"]:
                still_needed.append(required)
    
    return still_needed, ge_progress



def get_ge_areas_for_courses(conn, courses: list) -> dict:
    """
    Categorize courses into GE courses and non-GE courses.
    
    Args:
        conn: SQLAlchemy connection
        courses: List of course codes
        
    Returns:
        Dictionary with:
        - "GE_Classes": List of dicts with name, area, us1, us2, us3, lab_credit
        - "Everything Else": List of course names not found in GE courses
    """
    gc = ge_courses_table
    result = {
        "GE_Classes": [],
        "Everything Else": []
    }
    
    for course in courses:
        query = (
            select(gc.c.title, gc.c.area, gc.c.us1, gc.c.us2, gc.c.us3, gc.c.lab_credit)
            .where(gc.c.code == course)
            .limit(1)
        )
        row = conn.execute(query).fetchone()

        if row:
            result["GE_Classes"].append({
                "name": row.title,
                "area": row.area,
                "us1": bool(row.us1),
                "us2": bool(row.us2),
                "us3": bool(row.us3),
                "lab_credit": bool(row.lab_credit),
            })
        else:
            result["Everything Else"].append(course)
    
    return result


def get_ge_course_area(conn, course_code: str) -> str:
    """
    Query the database for a GE course's area by course code.
    
    Args:
        conn: SQLAlchemy connection
        course_code: The course code to look up
        
    Returns:
        The area or empty string if not found
    """
    gc = ge_courses_table
    query = (
        select(gc.c.area)
        .where(gc.c.code == course_code)
        .limit(1)
    )
    row = conn.execute(query).fetchone()
    return row.area if row else ""


def translate_ap_courses(conn, ap_credits: list) -> dict:
    """
    Look up AP exam credits in ap_articulation table and return their
    SJSU course equivalents.
    
    Args:
        conn: SQLAlchemy connection
        ap_credits: List of AP exam names from transcript
    
    Returns:
        Dict with:
        - "translated": List of dicts with ap_exam, sjsu_code, sjsu_title, ge_areas, units, us1-3, lab_credit, notes
        - "not_found": List of AP exam names that had no match
    """
    ap = ap_table
    result = {"translated": [], "not_found": []}
    
    for ap_exam in ap_credits:
        # Exact match
        query = (
            select(
                ap.c.sjsu_course_code,
                ap.c.sjsu_course_title,
                ap.c.ge_area,
                ap.c.units_granted,
                ap.c.us1,
                ap.c.us2,
                ap.c.us3,
                ap.c.lab_credit,
                ap.c.notes,
            )
            .where(ap.c.ap_exam == ap_exam)
            .order_by(ap.c.min_score.asc())
            .limit(1)
        )
        row = conn.execute(query).fetchone()
        
        # Fallback: fuzzy match
        if not row:
            query = (
                select(
                    ap.c.sjsu_course_code,
                    ap.c.sjsu_course_title,
                    ap.c.ge_area,
                    ap.c.units_granted,
                    ap.c.us1,
                    ap.c.us2,
                    ap.c.us3,
                    ap.c.lab_credit,
                    ap.c.notes,
                )
                .where(ap.c.ap_exam.like(f"%{ap_exam}%"))
                .order_by(ap.c.min_score.asc())
                .limit(1)
            )
            row = conn.execute(query).fetchone()
        
        if row:
            ge_areas = [a.strip() for a in row.ge_area.split(",")] if row.ge_area else []
            result["translated"].append({
                "ap_exam": ap_exam,
                "sjsu_code": row.sjsu_course_code,
                "sjsu_title": row.sjsu_course_title,
                "ge_areas": ge_areas,
                "units": row.units_granted,
                "us1": bool(row.us1),
                "us2": bool(row.us2),
                "us3": bool(row.us3),
                "lab_credit": bool(row.lab_credit),
                "notes": row.notes
            })
            logging.info(f"AP Translated: {ap_exam} → {row.sjsu_course_code} (GE: {ge_areas})")
        else:
            result["not_found"].append(ap_exam)
            logging.warning(f"AP exam not found in articulation table: {ap_exam}")
    
    return result


def invoke(transcript_str: str) -> str:
    """
    Analyze a transcript using structured prompt chaining.

    Args:
        transcript_str: The student's transcript text

    Returns:
        A detailed analysis of completed vs required classes
    """
    logging.info("Starting transcript analysis...")

    # Step 1: Extract major, classes, and AP credits from transcript
    ### FUTURE REGEX ###
    logging.info("Step 1: Extracting data from transcript...")
    extract_chain = extract_prompt | llm | JsonOutputParser()
    extracted_data = extract_chain.invoke({"transcript": transcript_str})
    
    major = extracted_data["major"]
    classes_taken = extracted_data["classes_taken"]
    ap_credits = extracted_data.get("ap_credits", [])
    print(major)
    logging.info(f"Found {len(classes_taken)} college courses and {len(ap_credits)} AP credits")

    # Open a single database connection for all queries
    with engine.connect() as conn:
        # Step 2: Translate AP credits to SJSU equivalents
        ap_translation = {"translated": [], "not_found": []}
        if ap_credits:
            logging.info("Step 2: Translating AP credits to SJSU equivalents...")
            ap_translation = translate_ap_courses(conn, ap_credits)
            
            # Add translated AP courses to the classes_taken list
            for t in ap_translation["translated"]:
                classes_taken.append(t["sjsu_code"])
            
            logging.info(f"Translated {len(ap_translation['translated'])} AP credits, {len(ap_translation['not_found'])} unmatched")
        
        # Step 3: Categorize classes into GE and non-GE
        logging.info("Step 3: Categorizing courses into GE and non-GE...")
        course_categorization = get_ge_areas_for_courses(conn, classes_taken)
        
        logging.info(f"GE classes taken: {len(course_categorization['GE_Classes'])}")
        logging.info(f"Non-GE classes taken: {len(course_categorization['Everything Else'])}")
    
    # Step 4: Find GE areas still needed (before exceptions)
    logging.info("Step 4: Finding GE areas still needed...")
    ge_areas_needed, ge_progress = get_ge_areas_still_needed(course_categorization)
    logging.info(f"GE areas still needed (before exceptions): {ge_areas_needed}")
    
    # Step 5: Apply major-specific GE exceptions
    major_exceptions = get_major_ge_exceptions(major)
    if major_exceptions["waived_areas"]:
        logging.info(f"Step 5: Applying major exceptions for '{major_exceptions['major_matched']}': waived {major_exceptions['waived_areas']}")
        waived = set(major_exceptions["waived_areas"])
        
        # Handle D1 specially: it only covers 3 of the 6 required D units
        # Full "D" waiver covers all 6 units
        if "D1" in waived and "D" not in waived:
            # D1 = partial waiver, add 3 units to D progress
            if "D" in ge_progress:
                ge_progress["D"]["earned"] += 3
                ge_progress["D"]["waived_units"] = 3
                logging.info("D1 waiver: added 3/6 units to Area D")
                # If now fully earned, remove from needed
                if ge_progress["D"]["earned"] >= ge_progress["D"]["required"]:
                    ge_areas_needed = [a for a in ge_areas_needed if a != "D"]
            waived.discard("D1")  # Don't try to remove "D1" from needed list (it's not in there)
        
        # Remove fully waived areas from the needed list
        ge_areas_needed = [area for area in ge_areas_needed if area not in waived]
        
        # Mark fully waived areas as complete in progress
        for area in waived:
            if area in ge_progress:
                ge_progress[area]["earned"] = ge_progress[area]["required"]
                ge_progress[area]["waived"] = True
        
        logging.info(f"GE areas still needed (after exceptions): {ge_areas_needed}")
    else:
        logging.info(f"Step 5: No major exceptions found for '{major}'")
    
    # Step 6: Compute American Institutions (US) area progress
    logging.info("Step 6: Computing US area progress...")
    us_progress = {
        "US1": {"satisfied": False, "courses": []},
        "US2": {"satisfied": False, "courses": []},
        "US3": {"satisfied": False, "courses": []},
    }

    # Check GE classes for US credit
    for ge_class in course_categorization["GE_Classes"]:
        if ge_class.get("us1"):
            us_progress["US1"]["satisfied"] = True
            us_progress["US1"]["courses"].append(ge_class["name"])
        if ge_class.get("us2"):
            us_progress["US2"]["satisfied"] = True
            us_progress["US2"]["courses"].append(ge_class["name"])
        if ge_class.get("us3"):
            us_progress["US3"]["satisfied"] = True
            us_progress["US3"]["courses"].append(ge_class["name"])

    # Check AP credits for US credit
    for ap in ap_translation.get("translated", []):
        if ap.get("us1"):
            us_progress["US1"]["satisfied"] = True
            us_progress["US1"]["courses"].append(f"{ap['ap_exam']} (AP)")
        if ap.get("us2"):
            us_progress["US2"]["satisfied"] = True
            us_progress["US2"]["courses"].append(f"{ap['ap_exam']} (AP)")
        if ap.get("us3"):
            us_progress["US3"]["satisfied"] = True
            us_progress["US3"]["courses"].append(f"{ap['ap_exam']} (AP)")

    us_areas_needed = [area for area, info in us_progress.items() if not info["satisfied"]]
    logging.info(f"US areas satisfied: {[a for a, i in us_progress.items() if i['satisfied']]}")
    logging.info(f"US areas still needed: {us_areas_needed}")
    
    # Step 7: Return the analysis
    result = {
        "major": major,
        "classes_taken": classes_taken,
        "ap_credits": {
            "original": ap_credits,
            "translated": ap_translation["translated"],
            "not_found": ap_translation["not_found"]
        },
        "categorization": course_categorization,
        "major_exceptions": major_exceptions,
        "ge_progress": ge_progress,
        "ge_areas_needed": ge_areas_needed,
        "us_progress": us_progress,
        "us_areas_needed": us_areas_needed,
        "upper_division_progress": {
            "R": {"satisfied": False, "courses": []},
            "S": {"satisfied": False, "courses": []},
            "V": {"satisfied": False, "courses": []},
        },
        "upper_division_needed": ["R", "S", "V"],
        "pe_progress": {"earned": 0, "required": 2, "courses": []},
    }
    
    logging.info("Transcript analysis complete")
    return json.dumps(result)
