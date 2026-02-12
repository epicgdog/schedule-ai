from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from sqlalchemy import create_engine, MetaData, select
from modules import get_major_ge_exceptions
import logging
from dotenv import load_dotenv
import os
import json
import re
import pandas as pd
import sqlite3

load_dotenv()

class course:
    def __init__(self, code: str, title: str, units: int, ge_area: list[str]):
        self.code: str = code
        self.title: str = title
        self.units: int = units
        self.ge_area: list[str] = ge_area
    
    def __str__(self):
        return f"{self.code} {self.title} {self.units} {self.ge_area}"

GE_UNITS_REQUIRED = {   
    "A":{"Areas":["A1", "A2", "A3"], "Units":9},
    "B":{"Areas":["B1", "B2", "B3", "B4"], "Units":9},
    "C":{"Areas":["C1", "C2"], "Units":9},
    "D":{"Areas":["D"], "Units":6},
    "F":{"Areas":["F"], "Units":3},
    "US":{"Areas":["US1","US2","US3"], "Units":6},
    "UPPER":{"Areas":["R", "S", "V"], "Units":9},
    "PE":{"Areas":["PE"], "Units":2}
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



def ge_processor_pipeline(ge_courses: list[course], major: str, conn: sqlite3.Connection) -> dict:
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
    """
    Find which GE areas are satisfied based on courses taken and exceptions.
    
    Args:
        ge_courses: List of course objects identified as GE
        major: Student major
        conn: Database connection
        
    Returns:
        Dict: JSON structure matching GE_UNITS_REQUIRED format with completed progress
    """
    # 1. Start with major exceptions (waived areas)
    # ge_exceptions returns a dict with "waived_data" containing the JSON structure
    exceptions_result = get_major_ge_exceptions(major, conn)
    ge_earned = exceptions_result.get("waived_data", {})
    if not ge_earned:
        ge_earned = {}

    # Define Mapping from detailed areas to Categories
    # Note: D1 maps to D. R, S, V map to UPPER.
    AREA_CATEGORY_MAP = {
        "A1": "A", "A2": "A", "A3": "A",
        "B1": "B", "B2": "B", "B3": "B", "B4": "B",
        "C1": "C", "C2": "C",
        "D": "D", "D1": "D", "D2": "D", "D3": "D",
        "F": "F",
        "US1": "US", "US2": "US", "US3": "US",
        "PE": "PE",
        "R": "UPPER", "S": "UPPER", "V": "UPPER"
    }

    # 2. Iterate courses and accumulate
    for course_obj in ge_courses:
        # course_obj.ge_area is a list of strings, e.g. ["C1", "US1"]
        for area_code in course_obj.ge_area:
            category = AREA_CATEGORY_MAP.get(area_code)
            
            # Special handling if needed (e.g. area "D" directly in string)
            if not category and area_code in ["A", "B", "C", "D", "E", "F", "PE"]:
                category = area_code
            elif not category:
                continue

            # Ensure category exists in dictionary
            if category not in ge_earned:
                ge_earned[category] = {"Areas": [], "Units": 0, "Courses": []}
            
            # Add area code if not already present
            if area_code not in ge_earned[category]["Areas"]:
                ge_earned[category]["Areas"].append(area_code)
            
            # Add units
            ge_earned[category]["Units"] += course_obj.units
            
            # Add course info if not already present (avoid duplicates)
            # Use a formatted string or dict? Just string for now as per previous simple implementation
            course_str = f"{course_obj.code} - {course_obj.title}"
            if course_str not in ge_earned[category]["Courses"]:
                 ge_earned[category]["Courses"].append(course_str)

    return ge_earned

def area_regex(txt: str) -> list[str]:
    """
    Extracts GE area codes from a transcript string.
    Example: "GE: A1 Oral Communication (1C)" -> ["A1"]
    Example: "GE: B1 + B3 Physical + Lab Sci" -> ["B1", "B3"]
    Example: "GE: 4 + US1 (D + US1)" -> ["D", "US1"]
    """
    if not txt or pd.isna(txt):
        return []
        
    if not isinstance(txt, str):
        txt = str(txt)

    # Regex to find standard GE codes
    # Looks for A1-A3, B1-B4, C1-C2, D, E, F, US1-US3, PE, R, S, V
    # We use word boundaries \b to avoid matching partial words (like "Social" -> S)
    pattern = r"\b(A[1-3]|B[1-4]|C[1-2]|D|E|F|US[1-3]|PE|R|S|V)\b"
    
    matches = re.findall(pattern, txt)
    
    # Deduplicate matches
    return list(set(matches))

def invoke(transcript_str: DataFrame) -> Dict:
    logging.info("Starting transcript analysis...")

    # Step 1: Extract major, classes, and AP credits from transcript
    logging.info("Step 1: Extracting data from transcript...")

    df = transcript_str
    # Handle list of DataFrames (from pd.read_html)
    if isinstance(df, list):
        if len(df) > 0:
            df = df[0]
        else:
            logging.error("Empty list of DataFrames provided to invoke")
            return {}

    # If df is not a DataFrame, convert or error?
    if not isinstance(df, pd.DataFrame):
        # Fallback if somehow still not a DataFrame, though unlikely given type hint
        try:
             df = pd.DataFrame(df)
        except:
             logging.error(f"Could not convert input {type(df)} to DataFrame")
             return {}

    
    df1 = df
    ## ADD MAJOR GRABBER OR SOME SHI IN THE FURTURE
    major = "Software Engineering"
    
    #cut off the first row of titles if necessary, assuming df doesn't have headers logic applied correctly
    # Or just skip first row as originally intended?
    if len(df1) > 1:
        df1 = df1.iloc[1:]

    CourseArray = []

    # Use len() for loop limit
    for row in range(len(df1)):
        # iloc uses 0-based integer position
        try:
            course_obj = course(
                code=str(df1.iloc[row, 0]),
                title=str(df1.iloc[row, 1]),
            # grade is at index 3? based on original code
            # units at index 4?
            # ge_area at index 8?
            # We must be careful about bounds
                units=float(df1.iloc[row, 4]) if pd.notna(df1.iloc[row, 4]) else 0,
                ge_area=area_regex(df1.iloc[row, 8]),
            )
             # Note: grade was used in original code line 122 but not in __init__?
             # class course: def __init__(self, code: str, title: str, units: int, ge_area: list[str]):
             # Original code line 122 passed `grade=...`.
             # BUT __init__ DOES NOT HAVE `grade`.
             # I need to remove `grade` from the call or add it to class.
             # I'll remove it since User defined class above and it doesn't have it.
            CourseArray.append(course_obj)
        except Exception as e:
            logging.error(f"Error parsing row {row}: {e}")
            continue

    logging.info(f"Found {len(CourseArray)} college courses")

    logging.info(f"Found {len(CourseArray)} college courses")

    GECourse = []
    MajorCourse = []

    # Use sqlite3 connection for the pipeline as it expects sqlite3 cursor
    with sqlite3.connect(os.getenv("DATABASE")) as conn:
        # Step 3: Categorize classes into GE and non-GE
        logging.info("Step 3: Categorizing courses into GE and non-GE...")

        for courseObj in CourseArray:
            if courseObj.ge_area:
                GECourse.append(courseObj)
            else:
                MajorCourse.append(courseObj)
        
        ge_course_dih = ge_processor_pipeline(GECourse, major, conn)
        gerard_ai_response_or_something = {}
        finalFrontend = {"Name": "Mansager Bathtub", "Major": major, "GE_Courses": ge_course_dih, "Major_Courses": gerard_ai_response_or_something}

    return finalFrontend
