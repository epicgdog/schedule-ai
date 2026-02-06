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