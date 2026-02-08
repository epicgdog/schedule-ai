from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
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
2. A list of all classes the student has taken and passed

Transcript:
{transcript}

Return ONLY a JSON object in this exact format:
{{
    "major": "extracted major name",
    "classes_taken": ["Class Code", "Class Code", ...]
}}

Be thorough and extract ALL classes mentioned in the transcript.""",
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
                    "CT title, area FROM ge_courses WHERE code = ? LIMIT 1",
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



def invoke(transcript_str: str) -> str:
    """
    Analyze a transcript using structured prompt chaining.

    Args:
        transcript_str: The student's transcript text

    Returns:
        A detailed analysis of completed vs required classes
    """
    logging.info("Starting transcript analysis...")

    # Step 1: Extract major and classes from transcript
    logging.info("Step 1: Extracting data from transcript...")
    extract_chain = extract_prompt | llm | JsonOutputParser()
    extracted_data = extract_chain.invoke({"transcript": transcript_str})

    major = extracted_data["major"]
    classes_taken = extracted_data["classes_taken"]

    # Step 2: Categorize classes into GE and non-GE
    logging.info("Step 2: Categorizing courses into GE and non-GE...")
    course_categorization = get_ge_areas_for_courses(classes_taken)
    
    logging.info(f"GE classes taken: {len(course_categorization['GE_Classes'])}")
    logging.info(f"Non-GE classes taken: {len(course_categorization['Everything Else'])}")
    
    # Step 3: Find GE areas still needed
    logging.info("Step 3: Finding GE areas still needed...")
    ge_areas_needed = get_ge_areas_still_needed(course_categorization)
    logging.info(f"GE areas still needed: {ge_areas_needed}")
    
    # Step 4: Return the analysis
    result = {
        "major": major,
        "classes_taken": classes_taken,
        "categorization": course_categorization,
        "ge_areas_needed": ge_areas_needed
    }
    
    logging.info("Transcript analysis complete")
    return json.dumps(result)



    # # Step 2: Get major requirements from database
    # logging.info(f"Step 2: Looking up requirements for major: {major}")
    # major_requirements = get_major_requirements(major)
    
    # if not major_requirements:
    #     logging.warning(f"No requirements found for major: {major}")
    #     return json.dumps({
    #         "major": major,
    #         "classes_taken": classes_taken,
    #         "classes_needed": [],
    #         "error": f"Major '{major}' not found in database"
    #     })
    
    # # Step 3: Use separation prompt to parse classes needed vs taken
    # logging.info("Step 3: Separating classes needed vs taken...")
    # combined_classes = {
    #     "classes_taken": classes_taken,
    #     "classes_needed_raw": major_requirements
    # }
    
    # separation_chain = seperation_prompt | llm | JsonOutputParser()
    # separation_result = separation_chain.invoke({"classes": json.dumps(combined_classes)})
    
    # # Step 4: Return the complete analysis
    # result = {
    #     "major": major,
    #     "classes_taken": classes_taken,
    #     "classes_needed": separation_result.get("classes_needed", [])
    # }
    
    # logging.info("Transcript analysis complete")
    # return json.dumps(result)




