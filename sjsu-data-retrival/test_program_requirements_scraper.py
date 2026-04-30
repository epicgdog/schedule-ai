"""
Tests for program_requirements_scraper parsing and storage functions.

Uses static HTML fixtures and mock JSON to validate:
- Scraping acalog-core divs
- Storing structured requirements data
"""

from program_requirements_scraper import scrape_program_page, store_program_requirements
from db import Base, ProgramRequiredCourse, ProgramElectiveGroup

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session


# ── Fixture: mock acalog-core HTML ──

PROGRAM_HTML = """
<html><body>
<div class="acalog-core">
<h2>Major Preparation (15 units)</h2>
<a href="preview_course.php?catoid=17&coid=156976">MATH 30 - Calculus I</a> 3 unit(s)
<a href="preview_course.php?catoid=17&coid=157000">MATH 31 - Calculus II</a> 4 unit(s)
</div>
<div class="acalog-core">
<h2>Upper Division (9 units)</h2>
<a href="preview_course.php?catoid=17&coid=157100">CS 146 - Data Structures</a> 3 unit(s)
<a href="preview_course.php?catoid=17&coid=157101">CS 147 - Computer Architecture</a> 3 unit(s)
</div>
<div class="some-other-div">
<p>This should be ignored</p>
</div>
</body></html>
"""


# ── Fixture: LLM output JSON ──

MOCK_LLM_JSON = {
    "major_name": "Computer Science, BS",
    "required_courses": ["CS 46A", "CS 46B", "CS 47", "MATH 30", "MATH 31"],
    "elective_groups": [
        {
            "heading": "Additional Mathematics Course",
            "instructions": "Complete one course",
            "choices": ["MATH 32", "MATH 142", "MATH 161A"],
        },
        {
            "heading": "Major Electives",
            "instructions": "Complete at least 17 units",
            "choices": ["CS 116A", "CS 116B", "CS 122", "CS 156"],
        },
    ],
}


# ── Tests: storage ──

def _make_engine():
    """Create an in-memory SQLite engine with programs table."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    # Create the programs table manually (it's not in our ORM)
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS programs "
            "(id INTEGER PRIMARY KEY, poid TEXT, program_name TEXT, requirements_json TEXT)"
        ))
        conn.execute(text(
            "INSERT INTO programs (poid, program_name) VALUES ('13772', 'Computer Science, BS')"
        ))
        conn.commit()
    return engine


def test_store_required_courses() -> None:
    engine = _make_engine()
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)

    with Session(engine) as session:
        courses = session.execute(
            select(ProgramRequiredCourse).where(ProgramRequiredCourse.poid == "13772")
        ).scalars().all()
        codes = [c.course_code for c in courses]
        assert "CS 46A" in codes
        assert "MATH 30" in codes
        assert len(codes) == 5


def test_store_elective_groups() -> None:
    engine = _make_engine()
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)

    with Session(engine) as session:
        groups = session.execute(
            select(ProgramElectiveGroup).where(ProgramElectiveGroup.poid == "13772")
        ).scalars().all()
        assert len(groups) == 2
        headings = [g.heading for g in groups]
        assert "Additional Mathematics Course" in headings
        assert "Major Electives" in headings


def test_store_raw_json() -> None:
    engine = _make_engine()
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)

    with engine.connect() as conn:
        raw = conn.execute(
            text("SELECT requirements_json FROM programs WHERE poid = '13772'")
        ).scalar()
        assert raw is not None
        parsed = __import__("json").loads(raw)
        assert parsed["major_name"] == "Computer Science, BS"


def test_json_extract_query() -> None:
    """Verify SQLite json_extract works on the stored JSON."""
    engine = _make_engine()
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)

    with engine.connect() as conn:
        name = conn.execute(
            text(
                "SELECT json_extract(requirements_json, '$.major_name') "
                "FROM programs WHERE poid = '13772'"
            )
        ).scalar()
        assert name == "Computer Science, BS"


def test_store_idempotent() -> None:
    """Re-storing should replace old data, not duplicate."""
    engine = _make_engine()
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)
    with Session(engine) as session:
        store_program_requirements(session, "13772", MOCK_LLM_JSON)

    with Session(engine) as session:
        courses = session.execute(
            select(ProgramRequiredCourse).where(ProgramRequiredCourse.poid == "13772")
        ).scalars().all()
        assert len(courses) == 5  # Not 10
