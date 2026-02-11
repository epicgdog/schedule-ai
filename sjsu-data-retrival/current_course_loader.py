"""
SJSU Current Course Loader

Loads scraped course schedule data into the sjsu_classes database table.
Uses scrapers.course_scraper for fetching and parsing.
"""

import argparse
import asyncio
import logging
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from scrapers.course_scraper import extract_courses, scrape_url

# Resolve paths relative to project root (parent of sjsu-data-retrival/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATABASE = str(PROJECT_ROOT / os.getenv("DATABASE", "db/sql.db"))


def database_setup() -> None:
    """Ensure the sjsu_classes table exists."""
    create_table = """
    CREATE TABLE IF NOT EXISTS sjsu_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        section_number INTEGER NOT NULL,
        class_number INTEGER NOT NULL UNIQUE,
        days TEXT,
        start_time TEXT,
        end_time TEXT,
        instructor TEXT,
        open_seats INTEGER NOT NULL
    )
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute(create_table)
            conn.commit()
            logger.info("sjsu_classes table ready")
    except sqlite3.OperationalError as e:
        logger.error("Failed to create table: %s", e)


def upsert_courses(courses: list[dict]) -> None:
    """Insert or update course rows into sjsu_classes."""
    insert_sql = """
    INSERT INTO sjsu_classes (course_name, section_number, class_number, days, start_time, end_time, instructor, open_seats)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (class_number) DO UPDATE SET
        course_name    = excluded.course_name,
        section_number = excluded.section_number,
        days           = excluded.days,
        start_time     = excluded.start_time,
        end_time       = excluded.end_time,
        instructor     = excluded.instructor,
        open_seats     = excluded.open_seats
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for c in courses:
            try:
                cursor.execute(insert_sql, (
                    c["course_name"],
                    c["section_number"],
                    c["class_number"],
                    c["days"],
                    c["start_time"],
                    c["end_time"],
                    c["instructor"],
                    c["open_seats"],
                ))
            except Exception as e:
                logger.error("Error inserting class %s: %s", c.get("class_number"), e)
        conn.commit()
        logger.info("Upserted %d course rows", len(courses))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load SJSU course schedule into database")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N courses (for testing)")
    parser.add_argument("--force", action="store_true", help="Clear existing data before loading")
    return parser.parse_args()


async def scrape_and_load(limit: int | None = None) -> None:
    """Scrape the schedule page and load courses into DB."""
    logger.info("Fetching SJSU schedule...")
    soup = scrape_url()
    if not soup:
        logger.error("Failed to fetch schedule page")
        return

    courses = extract_courses(soup, limit=limit)
    logger.info("Parsed %d courses", len(courses))
    upsert_courses(courses)
    logger.info("Done — %d courses loaded", len(courses))


def main() -> None:
    args = parse_args()
    database_setup()

    if args.force:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("DELETE FROM sjsu_classes")
            conn.commit()
            logger.info("Cleared existing sjsu_classes data")

    asyncio.run(scrape_and_load(limit=args.limit))


if __name__ == "__main__":
    main()
