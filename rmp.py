import requests
import json
import logging
from base64 import b64encode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def scrape_rmp(query, school_id="U2Nob29sLTg4MQ==", count=5):
    """
    Scrapes RateMyProfessors using their GraphQL API.
    
    Args:
        query (str): The professor's name to search for.
        school_id (str): Base64 encoded school ID (default is SJSU: School-881 -> U2Nob29sLTg4MQ==)
        count (int): Number of results to return.
    """
    url = "https://www.ratemyprofessors.com/graphql"
    
    # Common headers used by RMP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdDp0ZXN0" # Common public auth token for RMP
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
            "cursor": "", # Optional, can be empty or "YXJyYXljb25uZWN0aW9uOjE5"
            "query": {
                "text": query,
                "schoolID": school_id,
                "fallback": True
            }
        }
    }

    try:
        logging.info(f"Searching for '{query}' at school '{school_id}'...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for errors in the GraphQL response
        if 'errors' in data:
            logging.error(f"GraphQL Errors: {data['errors']}")
            return None

        # Extract teacher data
        teachers_data = data.get('data', {}).get('search', {}).get('teachers', {})
        edges = teachers_data.get('edges', [])
        
        results = []
        
        for edge in edges:
            node = edge.get('node', {})
            try:
                prof_data = {
                    "id": node.get('id'),
                    "firstName": node.get('firstName'),
                    "lastName": node.get('lastName'),
                    "avgRating": node.get('avgRating'),
                    "numRatings": node.get('numRatings'),
                    "avgDifficulty": node.get('avgDifficulty'),
                    "wouldTakeAgainPercent": node.get('wouldTakeAgainPercent'),
                    "department": node.get('department'),
                    "school": node.get('school', {}).get('name')
                }
                results.append(prof_data)
            except Exception as e:
                logging.warning(f"Failed to extract full details for a node, falling back to ID. Error: {e}")
                results.append({"id": node.get('id'), "error": "Extraction failed"})

        if not results:
            logging.info("No results found.")
            
        return results

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error: {e} - Response: {response.text}")
        return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Test queries
    
    for q in test_queries:
        print(f"\n--- Testing query: {q} ---")
        results = scrape_rmp("Sriram Rao")
        if results:
            print(json.dumps(results, indent=2))
        else:
            print("No data retrieved.")
