"""
AP Articulation Loader
Loads AP exam → SJSU course equivalency mappings into the database.

Usage:
    python ap_loader.py                  # Load from default data
    python ap_loader.py --url <URL>      # Scrape from a URL (TODO)
    python ap_loader.py --force          # Clear and reload all data
"""

import argparse
import logging
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

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


def database_setup_force() -> None:
    """Drop and recreate the ap_articulation table with updated schema."""
    drop_table = "DROP TABLE IF EXISTS ap_articulation"
    create_table = """
    CREATE TABLE IF NOT EXISTS ap_articulation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ap_exam TEXT NOT NULL,
        min_score INTEGER NOT NULL DEFAULT 3,
        max_score INTEGER,
        sjsu_course_code TEXT NOT NULL,
        sjsu_course_title TEXT,
        units_granted REAL,
        ge_area TEXT,
        us1 BOOLEAN,
        us2 BOOLEAN,
        us3 BOOLEAN,
        lab_credit BOOLEAN,
        notes TEXT,
        UNIQUE(ap_exam, min_score, sjsu_course_code)
    )
    """
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(drop_table)
        conn.execute(create_table)
        conn.commit()
        logger.info("ap_articulation table rebuilt")


# ──────────────────────────────────────────────────────
# Official SJSU AP Articulation Data
# Source: SJSU Catalog — Advanced Placement (AP) Exams
# https://catalog.sjsu.edu
#
# Format: (ap_exam, min_score, max_score, sjsu_course_code,
#          sjsu_course_title, units, ge_area, us1, us2, us3, lab_credit, notes)
#
# ge_area uses comma-separated values for multi-area credit
# Score-dependent exams have separate rows for each score range
# "Elective Credit" is used when no specific course equivalent exists
# us1 = American History, us2 = American Government, us3 = California Government
# lab_credit = True if the course satisfies a lab requirement (B3)
# ──────────────────────────────────────────────────────
#                                                                                                                                us1    us2    us3    lab
DEFAULT_AP_DATA = [
    # ── Art ──
    ("AP Art History", 3, 5, "ARTH 70A & ARTH 70B", "Art History Survey", 6.0, "C1,C2",                                        False, False, False, False, None),

    # ── Biology ──
    ("AP Biology", 3, 5, "BIOL 10", "The Living World", 6.0, "B2,B3",                                                          False, False, False, True,  None),

    # ── Calculus ──
    ("AP Calculus AB", 3, 5, "MATH 30", "Calculus I", 3.0, "B4",                                                               False, False, False, False, "Students may receive credit for only one calculus exam"),
    ("AP Calculus BC", 3, 5, "MATH 30 & MATH 31", "Calculus I & II", 7.0, "B4",                                                False, False, False, False, "Students may receive credit for only one calculus exam"),
    ("AP Calculus BC/AB Subscore", 3, 5, "MATH 30", "Calculus I", 3.0, "B4",                                                   False, False, False, False, "Students may receive credit for only one calculus exam"),

    # ── Chemistry ──
    ("AP Chemistry", 3, 5, "CHEM 30A", "General Chemistry", 6.0, "B1,B3",                                                      False, False, False, True,  None),

    # ── Chinese ──
    ("AP Chinese Language and Culture", 3, 5, "CHIN 1A", "Chinese Language", 6.0, "C2",                                        False, False, False, False, None),

    # ── Computer Science ──
    ("AP Computer Science A", 3, 5, "CS 46A", "Introduction to Programming", 3.0, None,                                        False, False, False, False, None),
    ("AP Computer Science Principles", 3, 5, "Elective Credit", "Elective Credit", 3.0, "B4",                                  False, False, False, False, "Beginning Fall 2018"),

    # ── English Language and Composition (score-dependent) ──
    ("AP English Language and Composition", 3, 3, "ENGL 1A", "First-Year Writing", 6.0, "A2",                                   False, False, False, False, "Score 3 only"),
    ("AP English Language and Composition", 4, 5, "ENGL 1A & ENGL 1B", "First-Year Writing & Argument and Analysis", 6.0, "A2,C2", False, False, False, False, "Score 4-5"),

    # ── English Literature and Composition (score-dependent) ──
    ("AP English Literature and Composition", 3, 3, "ENGL 1A & ENGL 10", "First-Year Writing & Intro to Literary Study", 6.0, "A2,C2", False, False, False, False, "Score 3"),
    ("AP English Literature and Composition", 4, 5, "ENGL 1A & ENGL 1B", "First-Year Writing & Argument and Analysis", 6.0, "A2,C2", False, False, False, False, "Score 4-5"),

    # ── Environmental Science ──
    ("AP Environmental Science", 3, 5, "Elective Credit", "Elective Credit", 4.0, "B1,B3",                                     False, False, False, True,  None),

    # ── European History ──
    ("AP European History", 3, 5, "HIST 10A & HIST 10B", "World Civilizations", 6.0, "C2,D",                                   False, False, False, False, None),

    # ── French ──
    ("AP French Language and Culture", 3, 5, "FREN 1A", "French Language", 6.0, "C2",                                          False, False, False, False, None),

    # ── German ──
    ("AP German Language and Culture", 3, 5, "GERM 1A", "German Language", 6.0, "C2",                                          False, False, False, False, None),

    # ── Human Geography ──
    ("AP Human Geography", 3, 5, "GEOG 10", "Introduction to Geography", 3.0, "D",                                             False, False, False, False, None),

    # ── Italian ──
    ("AP Italian Language and Culture", 3, 5, "ITAL 1A", "Italian Language", 6.0, "C2",                                        False, False, False, False, None),

    # ── Japanese ──
    ("AP Japanese Language and Culture", 3, 5, "JPN 1A", "Japanese Language", 6.0, "C2",                                        False, False, False, False, None),

    # ── Latin ──
    ("AP Latin", 3, 5, "Elective Credit", "Elective Credit", 6.0, "C2",                                                        False, False, False, False, None),

    # ── Macroeconomics ──
    ("AP Macroeconomics", 3, 5, "ECON 1A", "Principles of Macroeconomics", 4.0, "D",                                           False, False, False, False, None),

    # ── Microeconomics ──
    ("AP Microeconomics", 3, 5, "ECON 1B", "Principles of Microeconomics", 4.0, "D",                                           False, False, False, False, None),

    # ── Music Theory ──
    ("AP Music Theory", 3, 5, "Elective Credit", "Elective Credit", 6.0, None,                                                  False, False, False, False, "No GE credit"),

    # ── Government ──
    ("AP Comparative Government and Politics", 3, 5, "POLS 2", "Comparative Politics", 3.0, "D",                               False, False, False, False, None),
    ("AP U.S. Government and Politics", 3, 5, "Elective Credit", "Elective Credit", 3.0, "D",                                  False, True,  False, False, None),

    # ── Physics ──
    ("AP Physics 1", 3, 5, "PHYS 2A", "Fundamentals of Physics", 4.0, "B1,B3",                                                False, False, False, True,  "Max 8 units total if multiple physics exams taken"),
    ("AP Physics 2", 3, 5, "PHYS 2B", "Fundamentals of Physics", 4.0, "B1,B3",                                                False, False, False, True,  "Max 8 units total if multiple physics exams taken"),
    ("AP Physics C: Mechanics", 3, 5, "PHYS 50", "Mechanics", 4.0, "B1,B3",                                                    False, False, False, True,  "Max 8 units total if multiple physics exams taken"),
    ("AP Physics C: Electricity and Magnetism", 3, 5, "PHYS 51", "Electricity and Magnetism", 4.0, "B1,B3",                    False, False, False, True,  "Max 8 units total if multiple physics exams taken"),

    # ── Psychology ──
    ("AP Psychology", 3, 5, "PSYC 1", "General Psychology", 3.0, "D",                                                          False, False, False, False, None),

    # ── Spanish ──
    ("AP Spanish Language and Culture", 3, 5, "SPAN 1A", "Spanish Language", 6.0, "C2",                                        False, False, False, False, None),
    ("AP Spanish Literature and Culture", 3, 5, "SPAN 1B", "Spanish Literature", 6.0, "C2",                                    False, False, False, False, None),

    # ── Statistics ──
    ("AP Statistics", 3, 5, "STAT 95", "Elementary Statistics", 3.0, "B4",                                                     False, False, False, False, "Also equivalent to SOCI 15 or PH 67"),

    # ── Studio Art (no GE) ──
    ("AP Studio Art: 2D Design", 3, 5, "ART 12", "2D Design", 3.0, None,                                                       False, False, False, False, "No GE credit"),
    ("AP Studio Art: 3D Design", 3, 5, "Elective Credit", "Elective Credit", 3.0, None,                                        False, False, False, False, "No GE credit"),
    ("AP Studio Art: Drawing", 3, 5, "ART 24", "Drawing", 3.0, None,                                                           False, False, False, False, "No GE credit"),

    # ── History ──
    ("AP U.S. History", 3, 5, "HIST 20A & HIST 20B", "U.S. History", 6.0, "C2,D",                                             True,  False, False, False, None),
    ("AP World History: Modern", 3, 5, "Elective Credit", "Elective Credit", 3.0, "C2,D",                                     False, False, False, False, "Beginning Fall 2019"),

    # ── No Credit ──
    # Music Theory Aural/Non-Aural subscores, Research, Seminar — omitted (0 units / no credit)
]


def upsert_ap_data(data: list[tuple]) -> None:
    """Insert or update AP articulation data."""
    insert_sql = """
    INSERT INTO ap_articulation
        (ap_exam, min_score, max_score, sjsu_course_code, sjsu_course_title,
         units_granted, ge_area, us1, us2, us3, lab_credit, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(ap_exam, min_score, sjsu_course_code) DO UPDATE SET
        max_score = excluded.max_score,
        sjsu_course_title = excluded.sjsu_course_title,
        units_granted = excluded.units_granted,
        ge_area = excluded.ge_area,
        us1 = excluded.us1,
        us2 = excluded.us2,
        us3 = excluded.us3,
        lab_credit = excluded.lab_credit,
        notes = excluded.notes
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for row in data:
            cursor.execute(insert_sql, row)
        conn.commit()
        logger.info("Upserted %d AP articulation records", len(data))


def scrape_ap_articulation(url: str) -> list[tuple]:
    """
    TODO: Scrape AP articulation data from a URL.
    
    Once you find the articulation page, implement the scraping logic here.
    Should return a list of tuples matching the DEFAULT_AP_DATA format:
    (ap_exam, min_score, sjsu_course_code, sjsu_course_title, units, ge_area)
    """
    logger.warning("URL scraping not yet implemented: %s", url)
    logger.info("Falling back to default AP data")
    return DEFAULT_AP_DATA


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load AP articulation data into database")
    parser.add_argument("--url", type=str, help="URL to scrape AP articulation data from")
    parser.add_argument("--force", action="store_true", help="Clear and reload all data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_setup_force()

    if args.force:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("DELETE FROM ap_articulation")
            conn.commit()
            logger.info("Cleared existing ap_articulation data")

    if args.url:
        data = scrape_ap_articulation(args.url)
    else:
        data = DEFAULT_AP_DATA
        logger.info("Loading %d default AP articulation records", len(data))

    upsert_ap_data(data)
    logger.info("Done — %d AP articulation records loaded", len(data))


if __name__ == "__main__":
    main()
