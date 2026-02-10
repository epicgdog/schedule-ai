# helper functions

import sqlite3
import logging
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def parse_list(data_list):
    result = []
    for item in data_list:
        course_name = item[1]
        section_number = item[2]
        class_number = item[3]
        days = item[4]
        start_time = item[5]
        end_time = item[6]
        instructor = item[7]
        open_seats = item[8]

        result.append(
            {
                "course_name": course_name,
                "class_number": class_number,
                "section_number": section_number,
                "days": days,
                "start_time" : start_time,
                "end_time" : end_time,
                "instructor": instructor,
                "open_seats": open_seats,
            }
        )
    return result


# get scraped db; very basic edition
async def get_open_classes_for(course_name: str) -> list[dict]:
    """
    Get open classes for a given course name from the database.

    Args:
        course_name: Name of the course (e.g., "CS 47", "MATH 42"). Case insensitive.

    Returns:
        List of available class sections with open seats.
    """
    try:
        database = os.getenv("DATABASE")
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM sjsu_classes WHERE course_name = ? AND open_seats > 0"
            cursor.execute(sql, (course_name.upper(),))
            return parse_list(cursor.fetchall())
    except Exception as e:
        logging.error(f"Error retrieving open classes: {e}")
        return []


def get_major_ge_exceptions(major: str) -> dict:
    """
    Get GE area exceptions/waivers for a given major.
    
    Args:
        major: The student's major (e.g. "Computer Science", "Software Engineering")
    
    Returns:
        Dict with:
        - "waived_areas": list of GE area codes that are auto-satisfied
        - "notes": explanation text
        - "major_matched": the exact major name matched in the DB (or None)
    """
    try:
        database = os.getenv("DATABASE")
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            
            # Try exact match first
            cursor.execute(
                "SELECT major, degree, waived_ge_areas, notes FROM major_ge_exceptions WHERE major = ? LIMIT 1",
                (major,)
            )
            row = cursor.fetchone()
            
            if not row:
                # Fuzzy match — the LLM might say "Computer Science" but the table has "Computer Science"
                # or the table might have "Software Engineering" and the LLM says "Software Engineering, BS"
                cursor.execute(
                    "SELECT major, degree, waived_ge_areas, notes FROM major_ge_exceptions WHERE ? LIKE '%' || major || '%' OR major LIKE '%' || ? || '%' LIMIT 1",
                    (major, major)
                )
                row = cursor.fetchone()
            
            if row:
                waived_areas = [a.strip() for a in row[2].split(",")]
                return {
                    "waived_areas": waived_areas,
                    "notes": row[3],
                    "major_matched": f"{row[0]}, {row[1]}"
                }
            
            return {"waived_areas": [], "notes": None, "major_matched": None}
    except Exception as e:
        logging.error(f"Error retrieving major GE exceptions: {e}")
        return {"waived_areas": [], "notes": None, "major_matched": None}


async def get_ge_areas() -> list[str]:
    """Get unique GE areas."""
    try:
        database = os.getenv("DATABASE")
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            sql = "SELECT DISTINCT area FROM ge_courses ORDER BY area"
            cursor.execute(sql)
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error retrieving GE areas: {e}")
        return []


async def get_courses_by_ge(area: str) -> list[dict]:
    """Get all courses for a specific GE area."""
    try:
        database = os.getenv("DATABASE")
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            sql = "SELECT area, code, title FROM ge_courses WHERE area = ?"
            cursor.execute(sql, (area,))
            return [{"area": row[0], "code": row[1], "title": row[2]} for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error retrieving GE courses for area {area}: {e}")
        return []


async def get_open_ge_classes(area: str) -> list[dict]:
    """
    Get all OPEN class sections for a specific GE area.
    This performs a JOIN between ge_courses and sjsu_classes.
    """
    try:
        database = os.getenv("DATABASE")
        # Course codes in sjsu_classes might be formatted differently (e.g. "CS 47" vs "CS 047")
        # For now assuming exact string match on course code/name
        
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            # Join ge_courses and sjsu_classes on course code
            # sjsu_classes.course_name corresponds to ge_courses.code
            sql = """
            SELECT s.* 
            FROM sjsu_classes s
            JOIN ge_courses g ON s.course_name = g.code
            WHERE g.area = ? AND s.open_seats > 0
            """
            cursor.execute(sql, (area,))
            return parse_list(cursor.fetchall())
    except Exception as e:
        logging.error(f"Error retrieving open GE classes for area {area}: {e}")
        return []


async def get_instructor_rating(query: str, count: int = 5) -> list[dict]:
    """
    Scrapes RateMyProfessors using their GraphQL API to get instructor ratings.

    Args:
        query: The professor's name to search for.
        count: Number of results to return (default 5).
    """
    logger.info("getting instructor ratings")
    school_id = "U2Nob29sLTg4MQ=="
    url = "https://www.ratemyprofessors.com/graphql"

    # Common headers used by RMP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdDp0ZXN0",  # Common public auth token for RMP
    }

    # The GraphQL query provided
    graphql_query = """query TeacherSearchPaginationQuery(
  $count: Int!
  $cursor: String
  $query: TeacherSearchQuery!
) {
  search: newSearch {
    ...TeacherSearchPagination_search_1jWD3d
  }
}

fragment CardFeedback_teacher on Teacher {
  wouldTakeAgainPercent
  avgDifficulty
}

fragment CardName_teacher on Teacher {
  firstName
  lastName
}

fragment CardSchool_teacher on Teacher {
  department
  school {
    name
    id
  }
}

fragment TeacherBookmark_teacher on Teacher {
  id
  isSaved
}

fragment TeacherCard_teacher on Teacher {
  id
  legacyId
  avgRating
  numRatings
  ...CardFeedback_teacher
  ...CardSchool_teacher
  ...CardName_teacher
  ...TeacherBookmark_teacher
}

fragment TeacherSearchPagination_search_1jWD3d on newSearch {
  teachers(query: $query, first: $count, after: $cursor) {
    didFallback
    edges {
      cursor
      node {
        ...TeacherCard_teacher
        id
        __typename
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    resultCount
    filters {
      field
      options {
        value
        id
      }
    }
  }
}
"""

    payload = {
        "query": graphql_query,
        "operationName": "TeacherSearchPaginationQuery",
        "variables": {
            "count": count,
            "cursor": "",  # Optional, can be empty or "YXJyYXljb25uZWN0aW9uOjE5"
            "query": {"text": query, "schoolID": school_id, "fallback": True},
        },
    }

    try:
        logger.info(f"Searching for '{query}' at school '{school_id}'...")
        response = httpx.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Check for errors in the GraphQL response
        if "errors" in data:
            logger.error(f"GraphQL Errors: {data['errors']}")
            return []

        # Extract teacher data
        teachers_data = data.get("data", {}).get("search", {}).get("teachers", {})
        edges = teachers_data.get("edges", [])

        results = []

        for edge in edges:
            node = edge.get("node", {})
            try:
                prof_data = {
                    "id": node.get("id"),
                    "firstName": node.get("firstName"),
                    "lastName": node.get("lastName"),
                    "avgRating": node.get("avgRating"),
                    "numRatings": node.get("numRatings"),
                    "avgDifficulty": node.get("avgDifficulty"),
                    "wouldTakeAgainPercent": node.get("wouldTakeAgainPercent"),
                    "department": node.get("department"),
                    "school": node.get("school", {}).get("name"),
                }
                results.append(prof_data)
            except Exception as e:
                logger.warning(
                    f"Failed to extract full details for a node, falling back to ID. Error: {e}"
                )
                results.append({"id": node.get("id"), "error": "Extraction failed"})

        if not results:
            logger.info("No results found.")

        return results

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Error: {e} - Response: {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []