import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

# ── American Institutions course sets ────────────────────────────
# Source: SJSU Catalog — American Institutions Requirements
# US1 = U.S. History, US2 = U.S. Constitution, US3 = CA State/Local Gov
#
# Courses that satisfy US1 only:
US1_COURSES = {
    "AMS 10", "HIST 15", "HIST 20A", "HIST 20B",
    "HIST 170", "HIST 170S", "HIST 188",
}

# Courses that satisfy US2 + US3 (Constitution + CA Gov):
US23_COURSES = {
    "AMS 11", "POLS 1", "POLS 15", "POLS 16", "POLS 170V",
}

# Courses that satisfy US3 only (CA Government):
US3_ONLY_COURSES = {
    "HIST 189A", "HIST 189B", "POLS 102",
}

# Sequences that satisfy all US1+US2+US3 (both courses required):
# The 'B' course in each pair carries the US123 credit
US123_COURSES = {
    "AFAM 2A", "AFAM 2B",
    "AMS 1A", "AMS 1B",
    "AAS 33A", "AAS 33B",
    "CCS 10A", "CCS 10B",
}


def get_us_flags(course_code: str) -> tuple[bool, bool, bool]:
    """
    Determine US1, US2, US3 flags for a given course code.
    Returns (us1, us2, us3).
    """
    us1 = course_code in US1_COURSES or course_code in US123_COURSES
    us2 = course_code in US23_COURSES or course_code in US123_COURSES
    us3 = course_code in US23_COURSES or course_code in US3_ONLY_COURSES or course_code in US123_COURSES
    return us1, us2, us3


def parse_course_string(course_str: str) -> dict:
    """
    Parse a course string like 'CCS 74\u00a0-\u00a0Race and Ethnicity in Public Space'
    into {'code': 'CCS 74', 'name': 'Race and Ethnicity in Public Space'}.
    Removes non-breaking spaces (\u00a0).
    """
    # Replace non-breaking spaces with regular spaces
    cleaned = course_str.replace('\u00a0', ' ')
    
    # Split on " - " to separate code from name
    parts = cleaned.split(' - ', 1)
    if len(parts) == 2:
        return {
            'code': parts[0].strip(),
            'name': parts[1].strip()
        }
    else:
        # Fallback if format doesn't match expected pattern
        return {
            'code': cleaned.strip(),
            'name': ''
        }


def scrape_url(url: str) -> BeautifulSoup | None:
    """Fetch the URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as exc:
        print(f"Error fetching {url}: {exc}")
        return None


def extract_ge_areas(soup: BeautifulSoup) -> dict:
    """
    Extract GE Areas and their classes from the SJSU catalog page.
    Returns a dict: {Area: {Subarea: [class names]}} or {Area: {General: [class names]}}
    """
    ge_dict = defaultdict(lambda: defaultdict(list))
    
    # Find all h4 and h3 tags
    all_h4_tags = soup.find_all('h4')
    all_h3_tags = soup.find_all('h3')
    
    # For each h3 that's an area header
    for h3 in all_h3_tags:
        h3_text = h3.get_text(strip=True)
        area_match = re.match(r"^([A-Z])\.\s*(.+)", h3_text)
        
        if not area_match:
            continue
        
        area_letter = area_match.group(1)
        
        # Find the index of this h3
        h3_index = all_h3_tags.index(h3)
        next_h3_elem = all_h3_tags[h3_index + 1] if h3_index < len(all_h3_tags) - 1 else None
        
        # Collect h4 tags that belong to this area
        h4_for_area = []
        for h4 in all_h4_tags:
            if h4.find_previous('h3') == h3:
                h4_for_area.append(h4)
        
        if h4_for_area:
            # Pattern 1: Area with subareas (A, B, C)
            for h4 in h4_for_area:
                h4_text = h4.get_text(strip=True)
                subarea_match = re.match(r"^(\d+)\.\s*(.+)", h4_text)
                
                if subarea_match:
                    subarea_num = subarea_match.group(1)
                    subarea_id = f"{area_letter}{subarea_num}"
                    
                    # Find ul after this h4
                    ul = h4.find_next('ul')
                    if ul:
                        for li in ul.find_all('li', class_='acalog-course', recursive=False):
                            link = li.find('a')
                            if link:
                                course_name = link.get_text(strip=True)
                                parsed_course = parse_course_string(course_name)
                                # Add US and lab flags
                                us1, us2, us3 = get_us_flags(parsed_course['code'])
                                parsed_course['us1'] = us1
                                parsed_course['us2'] = us2
                                parsed_course['us3'] = us3
                                parsed_course['lab_credit'] = subarea_id == 'B3'
                                ge_dict[area_letter][subarea_id].append(parsed_course)
        else:
            # Pattern 2: Area without subareas (D, E, F, R, S, V)
            # Find first ul after this h3
            ul = h3.find_next('ul')
            if ul:
                for li in ul.find_all('li', class_='acalog-course', recursive=False):
                    link = li.find('a')
                    if link:
                        course_name = link.get_text(strip=True)
                        parsed_course = parse_course_string(course_name)
                        # Add US and lab flags
                        us1, us2, us3 = get_us_flags(parsed_course['code'])
                        parsed_course['us1'] = us1
                        parsed_course['us2'] = us2
                        parsed_course['us3'] = us3
                        parsed_course['lab_credit'] = False  # non-subarea sections aren't B3
                        ge_dict[area_letter][area_letter].append(parsed_course)
    
    return ge_dict


if __name__ == "__main__":
    TEST_URL = "https://catalog.sjsu.edu/preview_program.php?catoid=10&poid=2524"
    soup = scrape_url(TEST_URL)
    if soup:
        ge_areas = extract_ge_areas(soup)
        import json
        with open('ge_areas.json', 'w') as f:
            json.dump(ge_areas, f, indent=2)
