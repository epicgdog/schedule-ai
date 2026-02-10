from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from modules import get_major_ge_exceptions
import logging
from dotenv import load_dotenv
import os
import sqlite3
import json

load_dotenv()

GE_REQUIRED = ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C1/C2", "D", "E", "F"]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

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


# def get_major_requirements(major: str) -> str:
#     """
#     Query the database for major requirements by program name.
    
#     Args:
#         major: The major/program name to look up
        
#     Returns:
#         The requirements description or empty string if not found
#     """
#     database = os.getenv("DATABASE")
#     if not database:
#         logging.warning("DATABASE env var not set")
#         return ""
    
#     try:
#         with sqlite3.connect(database) as conn:
#             cursor = conn.cursor()
#             # Search for the major in the reqs table (course_name field contains program names)
#             cursor.execute(
#                 "SELECT description FROM reqs WHERE course_name LIKE ? LIMIT 1",
#                 (f"%{major}%",)
#             )
#             result = cursor.fetchone()
#             return result[0] if result else ""
#     except sqlite3.Error as e:
#         logging.error(f"Database error fetching requirements for {major}: {e}")
#         return ""
    



def get_ge_areas_still_needed(course_categorization: dict) -> list:
    """
    Find which GE areas are still needed based on courses taken.
    Handles special case for area C which requires C1, C2, and one additional C course.
    
    Args:
        course_categorization: Result from get_ge_areas_for_courses
        
    Returns:
        List of GE areas/subareas still needed
    """
    areas_taken = set()
    
    # Extract areas from taken GE classes
    for course in course_categorization["GE_Classes"]:
        subarea = course["area"]  # e.g., A1, B2, C1, D, E, etc.
        areas_taken.add(subarea)
    
    # Find what's still needed
    still_needed = []
    
    for required in GE_REQUIRED:
        if required == "C1/C2":
            # Special case: This represents the need for a third C course
            # Count how many unique C courses have been taken
            c_count = sum(1 for area in areas_taken if area in ["C1", "C2"])
            
            # Only add to needed if they don't have 3+ C courses
            if c_count < 3:
                still_needed.append(required)
        else:
            # Regular area requirement (A1, A2, A3, B1, B2, B3, B4, D, E, F)
            if required not in areas_taken:
                still_needed.append(required)
    
    return still_needed



def get_ge_areas_for_courses(courses: list) -> dict:
    """
    Categorize courses into GE courses and non-GE courses.
    
    Args:
        courses: List of course codes
        
    Returns:
        Dictionary with:
        - "GE_Classes": List of dicts with "name" and "area" keys
        - "Everything Else": List of course names not found in GE courses
    """
    database = os.getenv("DATABASE")
    if not database:
        logging.warning("DATABASE env var not set")
        return {"GE_Classes": [], "Everything Else": courses}
    
    result = {
        "GE_Classes": [],
        "Everything Else": []
    }
    
    try:
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            for course in courses:
                # Query for the course in ge_courses table
                cursor.execute(
                    "SELECT title, area FROM ge_courses WHERE code = ? LIMIT 1",
                    (course,)
                )
                row = cursor.fetchone()
                if row:
                    # Found in GE courses
                    result["GE_Classes"].append({
                        "name": row[0],
                        "area": row[1]
                    })
                else:
                    # Not found in GE courses
                    result["Everything Else"].append(course)
    except sqlite3.Error as e:
        logging.error(f"Database error categorizing courses: {e}")
        result["Everything Else"] = courses
    
    return result




def get_ge_course_area(course_code: str) -> str:
    """
    Query the database for a GE course's area by course code.
    
    Args:
        course_code: The course code to look up
        
    Returns:
        The area or empty string if not found
    """
    database = os.getenv("DATABASE")
    if not database:
        logging.warning("DATABASE env var not set")
        return ""
    
    try:
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Area FROM ge_courses WHERE code = ? LIMIT 1",
                (course_code,)
            )
            result = cursor.fetchone()
            return result[0] if result else ""
    except sqlite3.Error as e:
        logging.error(f"Database error fetching area for {course_code}: {e}")
        return ""


def translate_ap_courses(ap_credits: list) -> dict:
    """
    Look up AP exam credits in ap_articulation table and return their
    SJSU course equivalents.
    
    Args:
        ap_credits: List of AP exam names from transcript (e.g. ["AP Calculus AB", "AP English Language and Composition"])
    
    Returns:
        Dict with:
        - "translated": List of dicts {"ap_exam", "sjsu_code", "sjsu_title", "ge_areas" (list), "notes"}
        - "not_found": List of AP exam names that had no match in the table
    """
    database = os.getenv("DATABASE")
    if not database:
        logging.warning("DATABASE env var not set")
        return {"translated": [], "not_found": ap_credits}
    
    result = {"translated": [], "not_found": []}
    
    try:
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            for ap_exam in ap_credits:
                # Fuzzy match: try exact first, then LIKE
                cursor.execute(
                    "SELECT sjsu_course_code, sjsu_course_title, ge_area, notes FROM ap_articulation WHERE ap_exam = ? ORDER BY min_score ASC LIMIT 1",
                    (ap_exam,)
                )
                row = cursor.fetchone()
                
                if not row:
                    # Try a fuzzy match (the LLM might not use the exact name)
                    cursor.execute(
                        "SELECT sjsu_course_code, sjsu_course_title, ge_area, notes FROM ap_articulation WHERE ap_exam LIKE ? ORDER BY min_score ASC LIMIT 1",
                        (f"%{ap_exam}%",)
                    )
                    row = cursor.fetchone()
                
                if row:
                    # Parse comma-separated GE areas into a list
                    ge_areas = [a.strip() for a in row[2].split(",")] if row[2] else []
                    result["translated"].append({
                        "ap_exam": ap_exam,
                        "sjsu_code": row[0],
                        "sjsu_title": row[1],
                        "ge_areas": ge_areas,
                        "notes": row[3]
                    })
                    logging.info(f"AP Translated: {ap_exam} → {row[0]} (GE: {ge_areas})")
                else:
                    result["not_found"].append(ap_exam)
                    logging.warning(f"AP exam not found in articulation table: {ap_exam}")
    except sqlite3.Error as e:
        logging.error(f"Database error translating AP courses: {e}")
        result["not_found"] = ap_credits
    
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
    logging.info("Step 1: Extracting data from transcript...")
    extract_chain = extract_prompt | llm | JsonOutputParser()
    extracted_data = extract_chain.invoke({"transcript": transcript_str})

    major = extracted_data["major"]
    classes_taken = extracted_data["classes_taken"]
    ap_credits = extracted_data.get("ap_credits", [])
    
    logging.info(f"Found {len(classes_taken)} college courses and {len(ap_credits)} AP credits")

    # Step 2: Translate AP credits to SJSU equivalents
    ap_translation = {"translated": [], "not_found": []}
    if ap_credits:
        logging.info("Step 2: Translating AP credits to SJSU equivalents...")
        ap_translation = translate_ap_courses(ap_credits)
        
        # Add translated AP courses to the classes_taken list
        for t in ap_translation["translated"]:
            classes_taken.append(t["sjsu_code"])
        
        logging.info(f"Translated {len(ap_translation['translated'])} AP credits, {len(ap_translation['not_found'])} unmatched")
    
    # Step 3: Categorize classes into GE and non-GE
    logging.info("Step 3: Categorizing courses into GE and non-GE...")
    course_categorization = get_ge_areas_for_courses(classes_taken)
    
    logging.info(f"GE classes taken: {len(course_categorization['GE_Classes'])}")
    logging.info(f"Non-GE classes taken: {len(course_categorization['Everything Else'])}")
    
    # Step 4: Find GE areas still needed (before exceptions)
    logging.info("Step 4: Finding GE areas still needed...")
    ge_areas_needed = get_ge_areas_still_needed(course_categorization)
    logging.info(f"GE areas still needed (before exceptions): {ge_areas_needed}")
    
    # Step 5: Apply major-specific GE exceptions
    major_exceptions = get_major_ge_exceptions(major)
    if major_exceptions["waived_areas"]:
        logging.info(f"Step 5: Applying major exceptions for '{major_exceptions['major_matched']}': waived {major_exceptions['waived_areas']}")
        # Remove waived areas from the needed list
        # Handle D1 as partial D waiver — if D1 is waived, D is also waived
        waived = set(major_exceptions["waived_areas"])
        if "D1" in waived:
            waived.add("D")
        ge_areas_needed = [area for area in ge_areas_needed if area not in waived]
        logging.info(f"GE areas still needed (after exceptions): {ge_areas_needed}")
    else:
        logging.info(f"Step 5: No major exceptions found for '{major}'")
    
    # Step 6: Return the analysis
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
        "ge_areas_needed": ge_areas_needed
    }
    
    logging.info("Transcript analysis complete")
    return json.dumps(result)
