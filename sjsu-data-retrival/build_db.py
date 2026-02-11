"""
SJSU Data Retrieval — Build Database

Master script that runs all loaders to build/rebuild the full database.
Each loader creates its table and populates it from scraped or hardcoded data.

Usage:
    python build_db.py                  # Run all loaders
    python build_db.py --only ge ap     # Run specific loaders
    python build_db.py --force          # Force re-scrape everything
    python build_db.py --skip courses   # Skip slow loaders

Tables built:
    ge_courses          ← ge_loader.py
    ap_articulation     ← ap_loader.py
    major_ge_exceptions ← major_exceptions_loader.py
    reqs                ← major_loader.py
    sjsu_classes        ← current_course_loader.py
"""

import argparse
import asyncio
import logging
import sys
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Loader wrappers ──────────────────────────────────────────────
# Each function runs a loader's core logic without triggering its
# argparse (which would conflict with our own CLI args).

def load_ge(force: bool = False) -> None:
    """Load GE course data."""
    from ge_loader import database_setup, main as _main
    import ge_loader
    # Simulate args
    ge_loader.database_setup()

    from ge_loader import GE_URL
    from scrapers.ge_scraper import scrape_url, extract_ge_areas
    from ge_loader import extract_courses_from_ge_data, upsert_ge_courses
    import sqlite3, os

    database = os.getenv("DATABASE")
    soup = scrape_url(GE_URL)
    if not soup:
        logger.error("GE: Failed to scrape URL")
        return
    ge_data = extract_ge_areas(soup)
    if not ge_data:
        logger.error("GE: No data extracted")
        return
    courses = extract_courses_from_ge_data(ge_data)
    if force:
        with sqlite3.connect(database) as conn:
            conn.execute("DELETE FROM ge_courses")
            conn.commit()
    upsert_ge_courses(courses)
    logger.info("GE: loaded %d courses", len(courses))


def load_ap(force: bool = False) -> None:
    """Load AP articulation data."""
    from ap_loader import database_setup_force, upsert_ap_data, DEFAULT_AP_DATA
    database_setup_force()
    if force:
        import sqlite3, os
        database = os.getenv("DATABASE")
        with sqlite3.connect(database) as conn:
            conn.execute("DELETE FROM ap_articulation")
            conn.commit()
    upsert_ap_data(DEFAULT_AP_DATA)
    logger.info("AP: loaded %d records", len(DEFAULT_AP_DATA))


def load_major_exceptions(force: bool = False) -> None:
    """Load major-specific GE exceptions."""
    from major_exceptions_loader import database_setup, upsert_exceptions, EXCEPTIONS_DATA
    import sqlite3, os
    database = os.getenv("DATABASE")
    database_setup()
    if force:
        with sqlite3.connect(database) as conn:
            conn.execute("DELETE FROM major_ge_exceptions")
            conn.commit()
    upsert_exceptions(EXCEPTIONS_DATA)
    logger.info("Major Exceptions: loaded %d records", len(EXCEPTIONS_DATA))


def load_majors(force: bool = False) -> None:
    """Load major/program requirements (scrapes catalog — can be slow)."""
    from major_loader import (
        database_setup, existing_descriptions, parse_program_links,
        fetch_description, upsert_reqs, OUTPUT_MD,
    )
    database_setup()
    existing = existing_descriptions() if not force else {}
    programs = list(parse_program_links(OUTPUT_MD))
    logger.info("Majors: found %d programs, %d cached",
                len(programs), sum(1 for v in existing.values() if v))

    rows = []
    for idx, (title, url) in enumerate(programs, start=1):
        if existing.get(title):
            rows.append((title, existing[title]))
        else:
            desc = fetch_description(url)
            rows.append((title, desc))
            logger.info("Majors: scraped %s", title)
        if idx % 25 == 0:
            logger.info("Majors: %d/%d", idx, len(programs))

    upsert_reqs(rows)
    logger.info("Majors: loaded %d program requirements", len(rows))


def load_courses(force: bool = False) -> None:
    """Load current SJSU course schedule."""
    from current_course_loader import database_setup, scrape_and_load
    import sqlite3, os
    database = os.getenv("DATABASE")
    database_setup()
    if force:
        with sqlite3.connect(database) as conn:
            conn.execute("DELETE FROM sjsu_classes")
            conn.commit()
    asyncio.run(scrape_and_load())
    logger.info("Courses: done")


# ── Registry ─────────────────────────────────────────────────────

LOADERS = {
    "ge":         ("GE Courses",         load_ge),
    "ap":         ("AP Articulation",     load_ap),
    "exceptions": ("Major GE Exceptions", load_major_exceptions),
    "majors":     ("Major Requirements",  load_majors),
    "courses":    ("Current Courses",     load_courses),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the SJSU database by running all data loaders",
    )
    parser.add_argument(
        "--only", nargs="+", choices=LOADERS.keys(),
        help="Run only these loaders",
    )
    parser.add_argument(
        "--skip", nargs="+", choices=LOADERS.keys(),
        help="Skip these loaders",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-scrape / re-load all data",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Determine which loaders to run
    if args.only:
        to_run = {k: v for k, v in LOADERS.items() if k in args.only}
    elif args.skip:
        to_run = {k: v for k, v in LOADERS.items() if k not in args.skip}
    else:
        to_run = LOADERS

    total = len(to_run)
    logger.info("=" * 60)
    logger.info("SJSU Database Builder — running %d loader(s)", total)
    logger.info("=" * 60)

    failed = []
    for idx, (key, (name, loader_fn)) in enumerate(to_run.items(), start=1):
        logger.info("")
        logger.info("─" * 40)
        logger.info("[%d/%d] %s", idx, total, name)
        logger.info("─" * 40)
        start = time.time()
        try:
            loader_fn(force=args.force)
            elapsed = time.time() - start
            logger.info("[%d/%d] %s — done in %.1fs", idx, total, name, elapsed)
        except Exception as e:
            elapsed = time.time() - start
            logger.error("[%d/%d] %s — FAILED after %.1fs: %s", idx, total, name, elapsed, e)
            failed.append(name)

    logger.info("")
    logger.info("=" * 60)
    if failed:
        logger.warning("Completed with %d failure(s): %s", len(failed), ", ".join(failed))
        sys.exit(1)
    else:
        logger.info("All %d loaders completed successfully!", total)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
