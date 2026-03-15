"""Tests for course_tree graph builder."""

import sys

sys.path.insert(0, "server")
sys.path.insert(0, "sjsu-data-retrival")

from sqlalchemy import create_engine, text
from course_tree import build_course_tree
from db import Base


def _make_engine():
    """Create an in-memory SQLite with test data."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        # Programs table
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS programs "
                "(id INTEGER PRIMARY KEY, poid TEXT, program_name TEXT)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO programs (poid, program_name) "
                "VALUES ('100', 'Test CS, BS')"
            )
        )

        # Required courses
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS program_required_courses "
                "(id INTEGER PRIMARY KEY, poid TEXT, course_code TEXT)"
            )
        )
        for code in ["CS 46A", "CS 46B", "CS 146", "MATH 30", "MATH 42"]:
            conn.execute(
                text(
                    "INSERT INTO program_required_courses (poid, course_code) "
                    "VALUES ('100', :c)"
                ),
                {"c": code},
            )

        # Courses table
        courses = [
            ("1001", "CS 46A - Intro to Programming"),
            ("1002", "CS 46B - Data Structures"),
            ("1003", "CS 146 - DS & Algorithms"),
            ("1004", "MATH 30 - Calculus I"),
            ("1005", "MATH 42 - Discrete Math"),
            ("1006", "CS 49J - Java Programming"),  # NOT required
        ]
        for coid, name in courses:
            conn.execute(
                text("INSERT INTO courses (coid, course_name) VALUES (:coid, :name)"),
                {"coid": coid, "name": name},
            )

        # Prerequisites
        # CS 46B requires CS 46A
        conn.execute(
            text(
                "INSERT INTO course_prerequisites (course_coid, prerequisite_coid) "
                "VALUES ('1002', '1001')"
            )
        )
        # CS 146 requires CS 46B, MATH 30, MATH 42, CS 49J
        for prereq_coid in ["1002", "1004", "1005", "1006"]:
            conn.execute(
                text(
                    "INSERT INTO course_prerequisites (course_coid, prerequisite_coid) "
                    "VALUES ('1003', :p)"
                ),
                {"p": prereq_coid},
            )

        conn.commit()

    return engine


def test_nodes_are_only_required_courses() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    node_ids = {n["data"]["id"] for n in graph["nodes"]}
    assert node_ids == {"CS 46A", "CS 46B", "CS 146", "MATH 30", "MATH 42"}
    assert "CS 49J" not in node_ids  # Not in required set


def test_edges_filtered_to_required_set() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    edge_pairs = {(e["data"]["source"], e["data"]["target"]) for e in graph["edges"]}

    # These should exist (both ends in required set)
    assert ("CS 46A", "CS 46B") in edge_pairs
    assert ("CS 46B", "CS 146") in edge_pairs
    assert ("MATH 30", "CS 146") in edge_pairs
    assert ("MATH 42", "CS 146") in edge_pairs

    # CS 49J -> CS 146 should NOT exist (CS 49J not in required set)
    assert ("CS 49J", "CS 146") not in edge_pairs


def test_root_and_leaf_flags() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    nodes_by_id = {n["data"]["id"]: n["data"] for n in graph["nodes"]}

    # CS 46A and MATH 30 and MATH 42 are roots (no prereqs within required set)
    assert nodes_by_id["CS 46A"].get("is_root") is True
    assert nodes_by_id["MATH 30"].get("is_root") is True

    # CS 146 is a leaf (nothing depends on it)
    assert nodes_by_id["CS 146"].get("is_leaf") is True


def test_empty_program() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "nonexistent")
    assert graph["nodes"] == []
    assert graph["edges"] == []


def test_department_label() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    nodes_by_id = {n["data"]["id"]: n["data"] for n in graph["nodes"]}
    assert nodes_by_id["CS 46A"]["department"] == "CS"
    assert nodes_by_id["MATH 30"]["department"] == "MATH"


def test_program_name_returned() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    assert graph["program_name"] == "Test CS, BS"


def test_graph_has_no_duplicate_nodes_or_edges() -> None:
    engine = _make_engine()
    graph = build_course_tree(engine, "100")
    node_ids = [n["data"]["id"] for n in graph["nodes"]]
    edge_pairs = [(e["data"]["source"], e["data"]["target"]) for e in graph["edges"]]
    assert len(node_ids) == len(set(node_ids))
    assert len(edge_pairs) == len(set(edge_pairs))
