import argparse
import logging
import os
import sqlite3

from dotenv import load_dotenv
from scrappers.ge_scraper import scrape_url, extract_ge_areas


import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATABASE = os.getenv("DATABASE")
GE_URL = "https://catalog.sjsu.edu/preview_program.php?catoid=10&poid=2524"


def database_setup() -> None:
    """Ensure the ge_courses table exists."""
    create_table = """
    CREATE TABLE IF NOT EXISTS ge_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        UNIQUE(area, code, title)
    )
    """
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(create_table)
        conn.commit()
        logger.info("ge_courses table ready")


def extract_courses_from_ge_data(ge_data: dict) -> list[tuple[str, str, str]]:
    """
    Extract GE courses and return list of (area, code, title) tuples.
    
    Args:
        ge_data: Dict with structure {Area: {Subarea: [{code, name}, ...]}}
    
    Returns:
        List of (area, code, title) tuples
    """
    courses = []
    for area, subareas in ge_data.items():
        for subarea, course_list in subareas.items():
            for course in course_list:
                code = course.get('code', '').strip()
                title = course.get('name', '').strip()
                if code and title:
                    courses.append((subarea, code, title))
    return courses


def upsert_ge_courses(courses: list[tuple[str, str, str]]) -> None:
    """Insert or update courses into ge_courses table."""
    insert_sql = """
    INSERT INTO ge_courses (area, code, title)
    VALUES (?, ?, ?)
    ON CONFLICT(area, code, title) DO UPDATE SET area = excluded.area
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for area, code, title in courses:
            cursor.execute(insert_sql, (area, code, title))
        conn.commit()
        logger.info("upserted %d GE courses into ge_courses", len(courses))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load GE courses into database")
    parser.add_argument("--force", action="store_true", help="Re-insert all courses even if they exist")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_setup()
    
    logger.info(f"Scraping GE courses from {GE_URL}")
    soup = scrape_url(GE_URL)
    if not soup:
        logger.error("Failed to scrape URL")
        return
    
    logger.info("Extracting GE areas from HTML")
    ge_data = extract_ge_areas(soup)
    if not ge_data:
        logger.error("No GE data extracted")
        return
    
    courses = extract_courses_from_ge_data(ge_data)
    logger.info(f"parsed {len(courses)} GE courses")
    
    if args.force:
        # Clear existing data
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("DELETE FROM ge_courses")
            conn.commit()
            logger.info("cleared existing ge_courses")
    
    upsert_ge_courses(courses)
    logger.info("done")


if __name__ == "__main__":
    main()
