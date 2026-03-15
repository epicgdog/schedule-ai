"""
Course Detail Scraper — fetch and parse course info from SJSU catalog.

Reads COIDs from coids.txt, fetches each course's preview page, parses
name/units/description/prerequisites/corequisites/GE area, and upserts
into the database via SQLAlchemy.

Usage:
    python course_detail_scraper.py              # Scrape all COIDs
    python course_detail_scraper.py --limit 5    # Scrape first 5 only
"""

import argparse
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select

from db import Course, CourseCorequisite, CoursePrerequisite, Base, get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

PREVIEW_URL_TEMPLATE = "https://catalog.sjsu.edu/preview_course.php?catoid=17&coid={}"
REQUEST_DELAY_SECONDS = 0.5

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

COIDS_FILE = Path(__file__).resolve().parent / "coids.txt"

# Regex patterns
UNITS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*unit\(s\)")
GE_PATTERN = re.compile(r"Satisfies\s+(.+?)\.\s*$", re.MULTILINE)
COID_FROM_HREF = re.compile(r"coid=(\d+)")

# Keywords that mark the end of the description block
_SECTION_MARKERS = (
    "Satisfies",
    "Prerequisite",
    "Corequisite",
    "Grading",
    "Note(",
    "Cross-listed",
    "Lecture",
    "Lab",
    "Repeatable",
)


# ── Parsing functions ────────────────────────────────────────────


def parse_course_html(html: str) -> dict:
    """Parse a course preview page and return structured data.

    Returns a dict with keys:
        course_name, units, description, ge_area,
        prerequisites_text, corequisites_text,
        prerequisite_coids, corequisite_coids
    """
    soup = BeautifulSoup(html, "html.parser")

    course_name = _parse_course_name(soup)
    content = soup.find("td", class_="block_content") or soup.find("body")
    full_text = content.get_text(separator="\n") if content else ""

    return {
        "course_name": course_name,
        "units": _parse_units(full_text),
        "description": _parse_description(full_text, course_name),
        "ge_area": _parse_ge_area(full_text),
        "prerequisites_text": _parse_section_text(full_text, "Prerequisite"),
        "corequisites_text": _parse_section_text(full_text, "Corequisite"),
        "prerequisite_coids": _parse_section_coids(content, "Prerequisite"),
        "corequisite_coids": _parse_section_coids(content, "Corequisite"),
    }


def _parse_course_name(soup: BeautifulSoup) -> str | None:
    """Extract course name from h1#course_preview_title."""
    h1 = soup.find("h1", id="course_preview_title")
    if h1:
        return h1.get_text(strip=True)
    # Fallback: any h1
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else None


def _parse_units(text: str) -> str | None:
    """Extract units from page text."""
    match = UNITS_PATTERN.search(text)
    return match.group(1) if match else None


def _parse_description(text: str, course_name: str | None) -> str | None:
    """Extract description text between units and the first section marker."""
    lines = text.split("\n")
    desc_lines: list[str] = []
    capture = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip the course name line
        if course_name and stripped == course_name:
            continue

        # Start capturing after the units line
        if "unit(s)" in stripped:
            capture = True
            # Check if there's text after "unit(s)" on the same line
            after_units = stripped.split("unit(s)", 1)
            if len(after_units) > 1 and after_units[1].strip():
                desc_lines.append(after_units[1].strip())
            continue

        if capture:
            if any(marker in stripped for marker in _SECTION_MARKERS):
                break
            desc_lines.append(stripped)

    description = " ".join(desc_lines).strip()
    return description if description else None


def _parse_ge_area(text: str) -> str | None:
    """Extract GE area from 'Satisfies ...' text."""
    match = GE_PATTERN.search(text)
    if not match:
        return None
    area = match.group(1).strip()
    return area if area else None


def _parse_section_text(text: str, section_label: str) -> str | None:
    """Extract raw text for a labeled section like Prerequisite(s): or Corequisite(s):."""
    # Build pattern: "Prerequisite(s):" or "Corequisites:" etc.
    pattern = re.compile(
        rf"{section_label}(?:\(s\)|s)?:\s*(.*?)(?=(?:Prerequisite|Corequisite|Grading|Note\(|Cross-listed|$))",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None

    result = match.group(1).strip()
    # Clean up newlines
    result = re.sub(r"\s+", " ", result).strip()
    return result if result else None


def _parse_section_coids(content, section_label: str) -> list[str]:
    """Extract linked COIDs from <a> tags within a prerequisite/corequisite section.

    Walks the HTML looking for the section label, then collects coid links
    until the next section marker.
    """
    if content is None:
        return []

    coids: list[str] = []
    in_section = False

    for elem in content.descendants:
        if hasattr(elem, "name"):
            # Check for section start: <strong> containing the label
            if elem.name in ("strong", "b") and section_label in elem.get_text():
                in_section = True
                continue

            # Check for section end: next <strong>/<b> that isn't our section
            if in_section and elem.name in ("strong", "b"):
                label_text = elem.get_text()
                if section_label not in label_text:
                    break

            # Collect coid links within the section
            if in_section and elem.name == "a":
                href = elem.get("href", "")
                match = COID_FROM_HREF.search(href)
                if match:
                    coids.append(match.group(1))

    return coids


# ── I/O layer ────────────────────────────────────────────────────


def load_coids(path: Path = COIDS_FILE) -> list[str]:
    """Read COIDs from the text file."""
    text = path.read_text(encoding="utf-8").strip()
    return [line.strip() for line in text.split("\n") if line.strip()]


def fetch_course_html(coid: str) -> str | None:
    """Fetch the preview page HTML for a single COID."""
    url = PREVIEW_URL_TEMPLATE.format(coid)
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.error("Fetch failed: coid=%s error=%s", coid, exc)
        return None


def scrape_and_store(limit: int | None = None) -> None:
    """Main scraping loop: load COIDs, fetch pages, parse, upsert."""
    engine = get_engine()
    Base.metadata.create_all(engine)

    coids = load_coids()
    if limit:
        coids = coids[:limit]

    logger.info("Starting scrape of %d COIDs", len(coids))

    # Find already-scraped COIDs to skip
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        existing = set(
            row[0] for row in session.execute(select(Course.coid)).all()
        )

    new_coids = [c for c in coids if c not in existing]
    logger.info(
        "Skipping %d already-scraped, processing %d new",
        len(coids) - len(new_coids),
        len(new_coids),
    )

    stats = {"success": 0, "failed": 0, "skipped": len(coids) - len(new_coids)}

    for idx, coid in enumerate(new_coids, start=1):
        logger.info("(%d/%d) Fetching coid=%s", idx, len(new_coids), coid)

        html = fetch_course_html(coid)
        if not html:
            stats["failed"] += 1
            continue

        parsed = parse_course_html(html)
        if not parsed["course_name"]:
            logger.warning("No course name for coid=%s, skipping", coid)
            stats["failed"] += 1
            continue

        # Upsert course
        with Session(engine) as session:
            course = Course(
                coid=coid,
                course_name=parsed["course_name"],
                description=parsed["description"],
                units=parsed["units"],
                ge_area=parsed["ge_area"],
                prerequisites_text=parsed["prerequisites_text"],
                corequisites_text=parsed["corequisites_text"],
            )
            session.merge(course)

            # Upsert prerequisite links
            for prereq_coid in parsed["prerequisite_coids"]:
                existing_link = session.execute(
                    select(CoursePrerequisite).where(
                        CoursePrerequisite.course_coid == coid,
                        CoursePrerequisite.prerequisite_coid == prereq_coid,
                    )
                ).scalar_one_or_none()
                if not existing_link:
                    session.add(CoursePrerequisite(
                        course_coid=coid, prerequisite_coid=prereq_coid
                    ))

            # Upsert corequisite links
            for coreq_coid in parsed["corequisite_coids"]:
                existing_link = session.execute(
                    select(CourseCorequisite).where(
                        CourseCorequisite.course_coid == coid,
                        CourseCorequisite.corequisite_coid == coreq_coid,
                    )
                ).scalar_one_or_none()
                if not existing_link:
                    session.add(CourseCorequisite(
                        course_coid=coid, corequisite_coid=coreq_coid
                    ))

            session.commit()

        stats["success"] += 1
        logger.info(
            "  Saved: %s | Units=%s | GE=%s | Prereqs=%d links | Coreqs=%d links",
            parsed["course_name"],
            parsed["units"],
            parsed["ge_area"],
            len(parsed["prerequisite_coids"]),
            len(parsed["corequisite_coids"]),
        )

        # Rate limit
        if idx < len(new_coids):
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(
        "Done — success=%d, failed=%d, skipped=%d",
        stats["success"],
        stats["failed"],
        stats["skipped"],
    )


# ── CLI ──────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape SJSU course details")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of COIDs to process (for testing)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scrape_and_store(limit=args.limit)


if __name__ == "__main__":
    main()
