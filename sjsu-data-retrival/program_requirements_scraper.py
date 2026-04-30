"""
Program Requirements Scraper — scrape degree requirements + LLM extraction.

For each program (major) in the `programs` table:
1. Scrape the catalog page for `div.acalog-core` content
2. Send text to Groq for structured JSON extraction
3. Store raw JSON + normalized tables in Turso

Usage:
    python program_requirements_scraper.py              # All programs
    python program_requirements_scraper.py --limit 3    # First 3 only
    python program_requirements_scraper.py --force      # Re-process everything
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from groq import Groq
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db import (
    Base,
    ProgramElectiveGroup,
    ProgramRequiredCourse,
    get_engine,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

PROGRAM_URL_TEMPLATE = (
    "https://catalog.sjsu.edu/preview_program.php?catoid=17&poid={}"
)
REQUEST_DELAY_SECONDS = 0.5
LLM_DELAY_SECONDS = 2  # Groq free tier: ~30 req/min

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SYSTEM_PROMPT = """You are an expert academic data extraction system. I will provide you with unstructured text from a university catalog describing a specific major's degree requirements. Your task is to extract this information into a strict, validated JSON object.

Follow these rules exactly:
1. Identify the "Major Name" (if present in the text, otherwise leave as null).
2. Extract all strictly REQUIRED courses that every student in this major must take. Output ONLY the course codes (e.g., "CS 46A", "MATH 30") as an array of strings under the key "required_courses". Do not include units or titles.
3. Extract all ELECTIVE groups (e.g., "Approved Science Electives", "Additional Mathematics Course"). For each group, create an object in the "elective_groups" array containing:
   - "heading": The exact title of the elective section.
   - "instructions": The specific rule (e.g., "Complete one course", "Complete at least 8 units").
   - "choices": An array of the course codes listed as options under this heading.
4. Ignore general university requirements (like PE or GE) unless they are explicitly listed as major-specific preparation.
5. Output ONLY the raw JSON. Do not include markdown formatting, backticks, or conversational text.

Expected JSON format:
{
  "major_name": "string or null",
  "required_courses": ["string"],
  "elective_groups": [
    {
      "heading": "string",
      "instructions": "string",
      "choices": ["string"]
    }
  ]
}"""


# ── Scraping ─────────────────────────────────────────────────────


def scrape_program_page(poid: str) -> str | None:
    """Fetch a program page and extract text from div.acalog-core elements."""
    url = PROGRAM_URL_TEMPLATE.format(poid)
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Fetch failed: poid=%s error=%s", poid, exc)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    divs = soup.find_all("div", class_="acalog-core")

    if not divs:
        logger.warning("No acalog-core divs found for poid=%s", poid)
        return None

    parts = [div.get_text(separator="\n", strip=True) for div in divs]
    return "\n\n".join(parts)


# ── LLM Extraction ──────────────────────────────────────────────


MAX_LLM_RETRIES = 3
RATE_LIMIT_WAIT_SECONDS = 60


def extract_requirements_via_llm(scraped_text: str) -> dict | None:
    """Send scraped text to Groq and parse the structured JSON response.

    Retries with exponential backoff on rate-limit (429) errors.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not set")
        return None

    client = Groq(api_key=api_key)

    for attempt in range(1, MAX_LLM_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": scraped_text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("JSON parse failed: %s", exc)
            return None
        except Exception as exc:
            error_str = str(exc).lower()
            if "rate_limit" in error_str or "429" in error_str or "tokens per minute" in error_str:
                wait = RATE_LIMIT_WAIT_SECONDS * attempt
                logger.warning(
                    "Rate limited (attempt %d/%d), waiting %ds...",
                    attempt, MAX_LLM_RETRIES, wait,
                )
                time.sleep(wait)
                continue
            logger.error("Groq API error: %s", exc)
            return None

    logger.error("Exhausted %d retries due to rate limiting", MAX_LLM_RETRIES)
    return None


# ── Storage ──────────────────────────────────────────────────────


def store_program_requirements(
    session: Session, poid: str, data: dict
) -> None:
    """Upsert requirements JSON + normalized tables for one program."""
    raw_json = json.dumps(data, ensure_ascii=False)

    # Store raw JSON on the programs row
    session.execute(
        text("UPDATE programs SET requirements_json = :rj WHERE poid = :p"),
        {"rj": raw_json, "p": poid},
    )

    # Clear old normalized data for this poid (idempotent re-runs)
    session.execute(
        text("DELETE FROM program_required_courses WHERE poid = :p"),
        {"p": poid},
    )
    session.execute(
        text("DELETE FROM program_elective_groups WHERE poid = :p"),
        {"p": poid},
    )

    # Insert required courses
    for code in data.get("required_courses", []):
        if code and isinstance(code, str):
            session.add(ProgramRequiredCourse(poid=poid, course_code=code.strip()))

    # Insert elective groups
    for group in data.get("elective_groups", []):
        heading = group.get("heading", "")
        instructions = group.get("instructions", "")
        choices = group.get("choices", [])
        if heading:
            session.add(ProgramElectiveGroup(
                poid=poid,
                heading=heading,
                instructions=instructions,
                choices_json=json.dumps(choices, ensure_ascii=False),
            ))

    session.commit()


# ── Main pipeline ────────────────────────────────────────────────


def load_programs(engine) -> list[dict]:
    """Read all programs from the DB."""
    with Session(engine) as session:
        rows = session.execute(
            text("SELECT poid, program_name FROM programs ORDER BY program_name")
        ).fetchall()
        return [{"poid": r[0], "program_name": r[1]} for r in rows]


def scrape_and_store(limit: int | None = None, force: bool = False) -> None:
    """Main loop: for each program, scrape → LLM → store."""
    engine = get_engine()

    # Ensure new tables exist
    Base.metadata.create_all(engine)

    # Add requirements_json column to programs if it doesn't exist
    with engine.connect() as conn:
        cols = [
            row[1]
            for row in conn.execute(text("PRAGMA table_info(programs)")).fetchall()
        ]
        if "requirements_json" not in cols:
            conn.execute(
                text("ALTER TABLE programs ADD COLUMN requirements_json TEXT")
            )
            conn.commit()
            logger.info("Added requirements_json column to programs table")

    # Force: clear all existing data
    if force:
        logger.info("Force mode — clearing existing program requirements")
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM program_required_courses"))
            conn.execute(text("DELETE FROM program_elective_groups"))
            conn.execute(text("UPDATE programs SET requirements_json = NULL"))
            conn.commit()

    programs = load_programs(engine)
    if limit:
        programs = programs[:limit]

    # Find already-processed programs (have requirements_json)
    with Session(engine) as session:
        processed = set()
        for prog in programs:
            result = session.execute(
                text("SELECT requirements_json FROM programs WHERE poid = :p"),
                {"p": prog["poid"]},
            ).scalar()
            if result:
                processed.add(prog["poid"])

    new_programs = [p for p in programs if p["poid"] not in processed]
    logger.info(
        "Total: %d programs, skipping %d already-processed, processing %d new",
        len(programs),
        len(programs) - len(new_programs),
        len(new_programs),
    )

    stats = {"success": 0, "failed": 0, "skipped": len(programs) - len(new_programs)}

    for idx, prog in enumerate(new_programs, start=1):
        poid = prog["poid"]
        name = prog["program_name"]
        logger.info("(%d/%d) %s [poid=%s]", idx, len(new_programs), name, poid)

        # Step 1: Scrape
        scraped_text = scrape_program_page(poid)
        if not scraped_text:
            stats["failed"] += 1
            continue

        time.sleep(REQUEST_DELAY_SECONDS)

        # Step 2: LLM extraction
        data = extract_requirements_via_llm(scraped_text)
        if not data:
            stats["failed"] += 1
            continue

        # Step 3: Store
        try:
            with Session(engine) as session:
                store_program_requirements(session, poid, data)
            stats["success"] += 1

            req_count = len(data.get("required_courses", []))
            elect_count = len(data.get("elective_groups", []))
            logger.info(
                "  Saved: %d required courses, %d elective groups",
                req_count,
                elect_count,
            )
        except Exception as exc:
            logger.error("  Store failed: %s", exc)
            stats["failed"] += 1

        # Rate limit for Groq
        if idx < len(new_programs):
            time.sleep(LLM_DELAY_SECONDS)

    logger.info(
        "Done — success=%d, failed=%d, skipped=%d",
        stats["success"],
        stats["failed"],
        stats["skipped"],
    )


# ── CLI ──────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape program requirements via LLM")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of programs to process (for testing)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Clear existing data and re-process all programs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scrape_and_store(limit=args.limit, force=args.force)


if __name__ == "__main__":
    main()
