"""
Major GE Exceptions Loader
Loads major-specific GE exceptions/waivers into the database.

Source: SJSU Catalog — Exceptions for University Graduation Requirements (2021-2022)

Usage:
    python major_exceptions_loader.py           # Load all data
    python -m sjsu-data-retrival.major_exceptions_loader --force    # Clear and reload
"""

import argparse
import json
import logging
import os
import sqlite3
from pathlib import Path
import re
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


def database_setup() -> None:
    """Create the major_ge_exceptions table."""
    drop_table = "DROP TABLE IF EXISTS major_ge_exceptions"
    create_table = """
    CREATE TABLE IF NOT EXISTS major_ge_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        major TEXT NOT NULL,
        degree TEXT NOT NULL,
        waived_ge_areas TEXT NOT NULL,
        notes TEXT,
        catalog_year TEXT DEFAULT '2021-2022',
        UNIQUE(major, degree, catalog_year)
    )
    """
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(drop_table)
        conn.execute(create_table)
        conn.commit()
        logger.info("major_ge_exceptions table rebuilt")


# ──────────────────────────────────────────────────────
# Official SJSU Major GE Exceptions (2021-2022 Catalog)
# Source: Exceptions for University Graduation Requirements
#
# Format: (major, degree, waived_ge_areas, notes, catalog_year)
#
# waived_ge_areas: comma-separated list of GE areas auto-satisfied
#   - Standard GE: A1, A2, A3, B1, B2, B3, B4, C1, C2, D, E, F
#   - D1 = partial D satisfaction (with AMS Sequence)
#   - R = Area R (upper-division courses)
#   - PE = Physical Education
#   - S&V = Science & Values senior seminar
#
# ──────────────────────────────────────────────────────
EXCEPTIONS_DATA = [
    # ── Animation & Art ──
    ("Animation & Illustration", "BFA", "PE",
     "Physical Education Waived", "2021-2022"),

    # ── Aviation ──
    ("Aviation, Area of Specialization in Aviation Management", "BS", "B2,D1,PE",
     "B2 (Intensive Science with completion of major); D1 (with completion of AMS Sequence); PE Waived", "2021-2022"),

    # ── Biological Sciences ──
    ("Biological Sciences", "BA", "R",
     "Area R (completion of major, BIOL 115 or BIOL 118 and one of BIOL 160, BIOL 178, BIOL 135B, or MICR 127)", "2021-2022"),

    ("Biological Sciences, Microbiology Concentration with Chemistry Minor", "BS", "R",
     "Area R (completion of major, MICR 166 and MICR 127)", "2021-2022"),

    ("Biological Sciences, Molecular Biology Concentration with Chemistry Minor", "BS", "R",
     "Area R (completion of major, BIOL 115 and BIOL 135B)", "2021-2022"),

    ("Biological Sciences, Systems Physiology Concentration with Chemistry Minor", "BS", "R",
     "Area R (completion of major, BIOL 115 and BIOL 178)", "2021-2022"),

    ("Biological Sciences - Ecology and Evolution", "BS", "R",
     "Area R (completion of major, BIOL 115 and BIOL 160)", "2021-2022"),

    ("Biological Sciences - Marine Biology", "BS", "A3,R",
     "A3 met with completion of major; Area R (completion of major, BIOL 118)", "2021-2022"),

    # ── Chemistry ──
    ("Chemistry", "BA", "B2",
     "B2 (Intensive Science with completion of the major)", "2021-2022"),

    ("Chemistry", "BS", "B2,D1",
     "B2 (Intensive Science with completion of the major); D1 (with completion of AMS Sequence)", "2021-2022"),

    ("Chemistry, Biochemistry Concentration", "BS", "A3,R",
     "A3 met with completion of the major; Area R with CHEM 130A and CHEM 131B", "2021-2022"),

    # ── Computer Science ──
    ("Computer Science", "BS", "D1",
     "D1 (with completion of AMS Sequence)", "2021-2022"),

    # ── Dance ──
    ("Dance", "BA", "PE",
     "Physical Education with completion of the major", "2021-2022"),

    ("Dance", "BFA", "PE",
     "Physical Education with completion of the major", "2021-2022"),

    # ── Earth & Geo Sciences ──
    ("Earth System Science", "BS", "B2",
     "B2 (Intensive Science with completion of the major)", "2021-2022"),

    ("Geology", "BS", "A3,B2",
     "A3 met with completion of major; B2 (Intensive Science with completion of the major)", "2021-2022"),

    ("Meteorology", "BS", "B2,D1",
     "B2 (Intensive Science with completion of the major); D1 (with completion of AMS Sequence)", "2021-2022"),

    # ── Engineering ──
    ("Aerospace Engineering", "BS", "A3,B2,D1,PE, S, V",
     "A3 met; B2 (Intensive Science); D1 (AMS Sequence); PE Waived; S&V met in major (AE 171A/AE 171B or AE 172A/AE 172B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Biomedical Engineering", "BS", "A3,B2,D1,PE, S, V",
     "A3 met; B2 (Intensive Science); D1 (AMS Sequence); PE Waived; S&V met in major (ENGR 199A/ENGR 199B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Chemical Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (CMPE 195A/CMPE 195B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Civil Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Computer Engineering", "BS", "A3,D,PE, S, V",
     "A3 met; D (AMS Sequence); PE Waived; S&V met in major (CMPE 195A/CMPE 195B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Electrical Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (EE 198A/EE 198B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Industrial and Systems Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Interdisciplinary Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Materials Engineering", "BS", "A3,B2,D,PE, S, V",
     "A3 met; B2 (Intensive Science); D (AMS Sequence); PE Waived; S&V met in major (ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Mechanical Engineering", "BS", "A3, B2, D1, PE, S, V",
     "A3 met; B2 (Intensive Science); D1 (AMS Sequence); PE Waived; S&V met in major (ME 195A/ME 195B or ENGR 195C/ENGR 195D plus ENGR 195A/ENGR 195B)", "2021-2022"),

    ("Software Engineering", "BS", "A3, D1, PE, S, V",
     "A3 met; D1 (AMS Sequence); PE Waived; S&V met in major (CMPE 195A/CMPE 195B plus ENGR 195A/ENGR 195B)", "2021-2022"),

    # ── Engineering Technology ──
    ("Engineering Technology, Computer Network System Management Concentration", "BS", "B2, D1, PE",
     "B2 (Intensive Science with completion of the major); D1 (AMS Sequence); PE Waived", "2021-2022"),

    ("Engineering Technology, Manufacturing Systems Concentration", "BS", "B2,D1,PE",
     "B2 (Intensive Science with completion of the major); D1 (AMS Sequence); PE Waived", "2021-2022"),

    # ── Industrial Design ──
    ("Industrial Design", "BS", "PE",
     "Physical Education Waived", "2021-2022"),

    # ── Kinesiology ──
    ("Kinesiology, Area of Specialization in Exercise and Fitness Specialist", "BS", "B2,PE",
     "BIOL 65 and BIOL 66 fulfill Area B2; Physical Education with completion of the major", "2021-2022"),

    ("Kinesiology, Preparation for Teaching", "BS", "PE",
     "Physical Education with completion of the major", "2021-2022"),

    # ── Music ──
    ("Music, Composition Concentration", "BM", "PE",
     "Physical Education Waived", "2021-2022"),

    ("Music, Jazz Studies Concentration", "BM", "PE",
     "Physical Education Waived", "2021-2022"),

    ("Music, Performance - Keyboard (Piano)", "BM", "PE",
     "Physical Education Waived", "2021-2022"),

    # ── Nursing ──
    ("Nursing", "BS", "PE",
     "Physical Education Waived", "2021-2022"),

    # ── Physics ──
    ("Physics", "BA", "B2",
     "B2 (Intensive Science with completion of the major)", "2021-2022"),

    ("Physics, Preparation for Teaching Program", "BA", "B2",
     "B2 (Intensive Science with completion of the major)", "2021-2022"),

    ("Physics", "BS", "B2",
     "B2 (Intensive Science with completion of the major)", "2021-2022"),
]


def build_waiver_json(waived_codes_str: str) -> str:
    """
    Convert a comma-separated list of waived codes (e.g. 'A3,B2,D1,PE')
    into a JSON string adhering to the GE_UNITS_REQUIRED structure.
    Only includes the areas that are waived.
    """
    if not waived_codes_str:
        return "{}"

    codes = [c.strip() for c in waived_codes_str.split(",")]
    
    waivers = {
        "UPPER": {"Areas": [], "Units": 0},
        "PE": {"Areas": [], "Units": 0},
        "A": {"Areas": [], "Units": 0},
        "B": {"Areas": [], "Units": 0},
        "D": {"Areas": [], "Units": 0},
    }

    for code in codes:
        if code == "PE":
            waivers["PE"] = {"Areas": ["PE"], "Units": 2}
        
        elif code == "A3":
            # Part of A
            waivers["A"] = {"Areas": ["A3"], "Units": 3}
            
        elif code == "B2":
            # Part of B
            waivers["B"] = {"Areas": ["B2"], "Units": 3}
            
        elif code in ["D", "D1"]:
            # D or D1 -> Area D.
            waivers["D"] = {"Areas": ["D"], "Units": 6}

        elif code == "R":
            # Part of UPPER
            waivers["UPPER"]["Areas"].append("R")
            waivers["UPPER"]["Units"] += 3
            
        elif code == "S":
            # Part of UPPER
            waivers["UPPER"]["Areas"].append("S")
            waivers["UPPER"]["Units"] += 3
        elif code == "V":
            # Part of UPPER
            waivers["UPPER"]["Areas"].append("V")
            waivers["UPPER"]["Units"] += 3
        
        else:
            print(f"Warning: Unknown waiver code '{code}', skipping.")

    return json.dumps(waivers)


def upsert_exceptions(data: list[tuple]) -> None:
    """Insert or update major GE exceptions."""
    # Note: validation of JSON is done via build_waiver_json helper
    insert_sql = """
    INSERT INTO major_ge_exceptions (major, degree, waived_ge_areas, notes, catalog_year)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(major, degree, catalog_year) DO UPDATE SET
        waived_ge_areas = excluded.waived_ge_areas,
        notes = excluded.notes
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for row in data:

            # row is (major, degree, waived_ge_areas_str, notes, catalog_year)
            major, degree, raw_waivers, notes, year = row
            
            # Convert raw waivers to JSON
            json_waivers = build_waiver_json(raw_waivers)
            if major == "Software Engineering":
                print(json_waivers)
            cursor.execute(insert_sql, (major, degree, json_waivers, notes, year))
            
        conn.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load major GE exceptions into database")
    parser.add_argument("--force", action="store_true", help="Clear and reload all data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_setup()

    if args.force:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("DELETE FROM major_ge_exceptions")
            conn.commit()
            logger.info("Cleared existing major_ge_exceptions data")

    logger.info("Loading %d major GE exception records", len(EXCEPTIONS_DATA))
    upsert_exceptions(EXCEPTIONS_DATA)
    logger.info("Done — %d major GE exception records loaded", len(EXCEPTIONS_DATA))


if __name__ == "__main__":
    main()
