"""
SJSU Current Course Schedule Scraper

Fetches the Spring 2026 class schedule from SJSU and parses course data
from the HTML table rows.
"""

import re
import requests
from bs4 import BeautifulSoup


SCHEDULE_URL = "https://www.sjsu.edu/classes/schedules/spring-2026.php"
SECTION_PATTERN = r"\(Section (\d+)\)"


def scrape_url(url: str = SCHEDULE_URL) -> BeautifulSoup | None:
    """Fetch the schedule page and return a BeautifulSoup object."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"Error fetching {url}: {exc}")
        return None


def parse_course_row(info: list) -> dict | None:
    """
    Parse a single table row (list of <td> elements) into a course dict.

    Returns:
        Dict with keys: course_name, section_number, class_number,
                        days, start_time, end_time, instructor, open_seats
        or None if parsing fails.
    """
    try:
        full_course_name = info[0].string
        course_name = full_course_name
        if "(" in full_course_name:
            course_name = full_course_name[: full_course_name.index("(")].strip()

        match = re.search(SECTION_PATTERN, full_course_name)
        section_number = int(match.group(1)) if match else None
        class_number = int(info[1].string)
        days = info[7].string
        times = info[8].string

        if times == "TBA":
            start_time = -1
            end_time = -1
        else:
            st, en = times.split("-")
            start_time = st.strip()
            end_time = en.strip()

        instructor = info[9].string
        open_seats = int(info[12].string)

        return {
            "course_name": course_name,
            "section_number": section_number,
            "class_number": class_number,
            "days": days,
            "start_time": start_time,
            "end_time": end_time,
            "instructor": instructor,
            "open_seats": open_seats,
        }
    except Exception as exc:
        print(f"Error parsing row: {exc}")
        return None


def extract_courses(soup: BeautifulSoup, limit: int | None = None) -> list[dict]:
    """
    Extract course data from all table rows in the schedule page.

    Args:
        soup: Parsed HTML of the schedule page
        limit: Optional max number of rows to parse (for testing)

    Returns:
        List of course dicts.
    """
    table_rows = soup.find_all("tr")
    rows = table_rows[1:]  # skip header row
    if limit is not None:
        rows = rows[:limit]

    courses = []
    for row in rows:
        info = row.find_all("td")
        if not info:
            continue
        course = parse_course_row(info)
        if course:
            courses.append(course)

    return courses


if __name__ == "__main__":
    soup = scrape_url()
    if soup:
        courses = extract_courses(soup, limit=5)
        for c in courses:
            print(f"{c['course_name']} (Section {c['section_number']}) - {c['days']} {c['start_time']}-{c['end_time']}")
