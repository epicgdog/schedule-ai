import argparse
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from dotenv import load_dotenv

from description import extract_program_block, scrape_url

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATABASE = os.getenv("DATABASE")
OUTPUT_MD = Path(__file__).resolve().parent / "output.md"


def database_setup() -> None:
    """Ensure the reqs table exists."""
    create_table = """
    CREATE TABLE IF NOT EXISTS reqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(create_table)
        conn.commit()
        logger.info("reqs table ready")


def existing_descriptions() -> dict:
    """Return a mapping of course_name -> description from reqs."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT course_name, description FROM reqs")
        return {name: desc or "" for name, desc in cursor.fetchall()}


def parse_program_links(md_path: Path) -> Iterable[Tuple[str, str]]:
    """Extract (title, url) pairs from markdown links."""
    text = md_path.read_text(encoding="utf-8")
    pairs = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", text)
    # Preserve order while removing duplicates
    seen = set()
    ordered = []
    for title, url in pairs:
        if (title, url) in seen:
            continue
        seen.add((title, url))
        ordered.append((title.strip(), url.strip()))
    return ordered


def fetch_description(url: str) -> str:
    """Fetch and return plain-text block for a program URL."""
    soup = scrape_url(url)
    if not soup:
        return ""
    block = extract_program_block(soup)
    return block or ""


def upsert_reqs(rows: Sequence[Tuple[str, str]]) -> None:
    """Insert or update course_name/description rows into reqs table."""
    insert_sql = """
    INSERT INTO reqs (course_name, description)
    VALUES (?, ?)
    ON CONFLICT(course_name) DO UPDATE SET description = excluded.description
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for course_name, description in rows:
            cursor.execute(insert_sql, (course_name, description))
        conn.commit()
        logger.info("upserted %d rows into reqs", len(rows))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load program requirements into reqs table")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N programs (for testing)")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if a row already exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_setup()
    existing = existing_descriptions()
    if args.force:
        existing = {}
    programs = list(parse_program_links(OUTPUT_MD))
    if args.limit is not None:
        programs = programs[: args.limit]
    logger.info("found %d program links", len(programs))
    logger.info("skipping %d already-populated programs", sum(1 for v in existing.values() if v))

    rows: List[Tuple[str, str]] = []
    try:
        for idx, (title, url) in enumerate(programs, start=1):
            if existing.get(title):
                logger.info("skip cached %s", title)
                rows.append((title, existing[title]))
            else:
                desc = fetch_description(url)
                rows.append((title, desc))
                logger.info("scraped %s", title)

            if idx % 25 == 0:
                logger.info("processed %d/%d", idx, len(programs))
    except KeyboardInterrupt:
        logger.warning("interrupted; writing progress so far (%d rows)", len(rows))

    upsert_reqs(rows)
    logger.info("done")


if __name__ == "__main__":
    main()
