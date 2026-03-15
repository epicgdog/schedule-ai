"""
Tests for course_detail_scraper parsing functions.

Uses static HTML fixtures modeled after real `preview_course.php` pages
to validate extraction of course name, units, description, GE area,
prerequisites (text + linked COIDs), and corequisites.
"""

from course_detail_scraper import parse_course_html


# ── Fixture: simple course, no prereqs (modeled on KIN 1) ──

SIMPLE_HTML = """
<html><body>
<h1 id="course_preview_title">KIN 1 - Adapted Physical Activities</h1>
<hr>
<td class="block_content">
<em>1</em> <em>unit(s)</em><br>
Structured individualized physical activities to enhance physical/motor
fitness and develop an active, health-oriented lifestyle for students
unable to participate in the general activity program.<br>
<br>
<em>Satisfies</em> <em>PE: Physical Education.</em><br>
<br>
<em>Repeatable for credit with instructor consent.</em><br>
<br>
<strong>Grading:</strong> Letter Graded<br>
<br>
<strong>Note(s):</strong> Movement Area 2 Fitness<br>
</td>
</body></html>
"""


# ── Fixture: course with prereqs, coreqs, GE area (modeled on MATH 19) ──

FULL_HTML = """
<html><body>
<h1 id="course_preview_title">MATH 19 - Precalculus</h1>
<hr>
<td class="block_content">
<em>5</em> <em>unit(s)</em><br>
Preparation for calculus: polynomial, rational, exponential, logarithmic
and trigonometric functions; analytic geometry.<br>
<br>
<em>Lecture 4 hours/Lab 3 hours.</em><br>
<br>
<em>Satisfies</em> <em>GE Area: 2. Mathematical Concepts and Quantitative Reasoning (Formerly Area B4).</em><br>
<br>
<strong>Prerequisite(s):</strong> <a href="preview_course.php?catoid=17&coid=156900">MATH 8</a> with a grade of C- or better, or Math Enrollment Category M-I, M-II, or M-III.<br>
<strong>Corequisite(s):</strong> <a href="preview_course.php?catoid=17&coid=170001">MATH 1019S</a> required as a corequisite for Enrollment Category M-III, and recommended for Enrollment Category M-II.<br>
<strong>Grading:</strong> ABC-/No Credit.<br>
<br>
<strong>Note(s):</strong> A grade of C- (1.7) or better is required to satisfy GE Area 2.<br>
</td>
</body></html>
"""


# ── Fixture: course with multiple prerequisite links ──

MULTI_PREREQ_HTML = """
<html><body>
<h1 id="course_preview_title">CS 146 - Data Structures and Algorithms</h1>
<hr>
<td class="block_content">
<em>3</em> <em>unit(s)</em><br>
Implementations of advanced data structures including balanced search trees,
hash tables, priority queues, and graphs.<br>
<br>
<strong>Prerequisite(s):</strong> <a href="preview_course.php?catoid=17&coid=157100">CS 46B</a> and
<a href="preview_course.php?catoid=17&coid=156950">MATH 30</a> (or
<a href="preview_course.php?catoid=17&coid=156951">MATH 30P</a>),
each with a grade of C- or better.<br>
<strong>Grading:</strong> Letter Graded<br>
</td>
</body></html>
"""


# ── Fixture: empty/minimal page ──

EMPTY_HTML = """
<html><body>
<h1 id="course_preview_title">PLACEHOLDER 999 - No Content</h1>
<hr>
<td class="block_content">
</td>
</body></html>
"""


# ── Fixture: fractional units ──

FRACTIONAL_UNITS_HTML = """
<html><body>
<h1 id="course_preview_title">MUSC 100 - Chamber Music</h1>
<hr>
<td class="block_content">
<em>0.5</em> <em>unit(s)</em><br>
Performance of chamber music literature.<br>
<br>
<strong>Grading:</strong> Letter Graded<br>
</td>
</body></html>
"""


# ── Tests: course name ──

def test_parse_course_name_simple() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["course_name"] == "KIN 1 - Adapted Physical Activities"


def test_parse_course_name_full() -> None:
    result = parse_course_html(FULL_HTML)
    assert result["course_name"] == "MATH 19 - Precalculus"


# ── Tests: units ──

def test_parse_units_simple() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["units"] == "1"


def test_parse_units_full() -> None:
    result = parse_course_html(FULL_HTML)
    assert result["units"] == "5"


def test_parse_units_fractional() -> None:
    result = parse_course_html(FRACTIONAL_UNITS_HTML)
    assert result["units"] == "0.5"


def test_parse_units_missing() -> None:
    result = parse_course_html(EMPTY_HTML)
    assert result["units"] is None


# ── Tests: description ──

def test_parse_description_simple() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert "physical activities" in result["description"].lower()
    assert "Grading" not in result["description"]


def test_parse_description_full() -> None:
    result = parse_course_html(FULL_HTML)
    assert "Preparation for calculus" in result["description"]
    assert "Prerequisite" not in result["description"]


def test_parse_description_empty() -> None:
    result = parse_course_html(EMPTY_HTML)
    assert result["description"] is None or result["description"] == ""


# ── Tests: GE area ──

def test_parse_ge_area_pe() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert "PE" in result["ge_area"]


def test_parse_ge_area_full() -> None:
    result = parse_course_html(FULL_HTML)
    assert "Mathematical Concepts" in result["ge_area"]


def test_parse_ge_area_missing() -> None:
    result = parse_course_html(MULTI_PREREQ_HTML)
    assert result["ge_area"] is None


# ── Tests: prerequisites text ──

def test_parse_prerequisites_text() -> None:
    result = parse_course_html(FULL_HTML)
    assert "MATH 8" in result["prerequisites_text"]
    assert "M-III" in result["prerequisites_text"]


def test_parse_prerequisites_text_missing() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["prerequisites_text"] is None


# ── Tests: prerequisite COIDs (linked) ──

def test_parse_prerequisite_coids_single() -> None:
    result = parse_course_html(FULL_HTML)
    assert "156900" in result["prerequisite_coids"]


def test_parse_prerequisite_coids_multiple() -> None:
    result = parse_course_html(MULTI_PREREQ_HTML)
    coids = result["prerequisite_coids"]
    assert "157100" in coids  # CS 46B
    assert "156950" in coids  # MATH 30
    assert "156951" in coids  # MATH 30P


def test_parse_prerequisite_coids_none() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["prerequisite_coids"] == []


# ── Tests: corequisites ──

def test_parse_corequisites_text() -> None:
    result = parse_course_html(FULL_HTML)
    assert "MATH 1019S" in result["corequisites_text"]


def test_parse_corequisites_text_missing() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["corequisites_text"] is None


def test_parse_corequisite_coids() -> None:
    result = parse_course_html(FULL_HTML)
    assert "170001" in result["corequisite_coids"]


def test_parse_corequisite_coids_none() -> None:
    result = parse_course_html(SIMPLE_HTML)
    assert result["corequisite_coids"] == []
