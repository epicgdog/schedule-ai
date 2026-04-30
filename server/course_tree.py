"""
Course prerequisite tree builder.

Builds a Cytoscape.js-compatible graph for a program's required courses,
filtering prerequisite edges to only courses within the required set.

Usage:
    from course_tree import build_course_tree
    graph = build_course_tree(engine, poid="13772")
    # Returns {"nodes": [...], "edges": [...]}
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def build_course_tree(engine: Engine, poid: str) -> dict:
    """Build a prerequisite graph for a program's required courses.

    Returns Cytoscape.js-compatible elements:
        {
            "nodes": [{"data": {"id": "CS 46A", "label": "CS 46A"}}],
            "edges": [{"data": {"source": "CS 46A", "target": "CS 146"}}]
        }

    Edges are filtered so both source and target must be in the required set.
    """
    with engine.connect() as conn:
        # 1. Get distinct required course codes for this program
        required_codes = _get_required_codes(conn, poid)
        if not required_codes:
            return {"nodes": [], "edges": [], "program_name": None}

        # Get program name
        program_name = conn.execute(
            text("SELECT program_name FROM programs WHERE poid = :p"),
            {"p": poid},
        ).scalar()

        # 2. Map course_code -> coid for all required courses
        code_to_coid = _map_codes_to_coids(conn, required_codes)

        # 3. Build reverse map: coid -> course_code
        coid_to_code = {coid: code for code, coid in code_to_coid.items()}

        # 4. For each required course, get prerequisites and filter
        edges = _build_filtered_edges(conn, code_to_coid, coid_to_code, required_codes)

        # 5. Build nodes
        nodes_data: list[dict[str, Any]] = []
        for code in required_codes:
            node_data: dict[str, Any] = {"id": code, "label": code}
            nodes_data.append(node_data)

        # 6. Identify root nodes (no incoming edges) for styling
        targets = {e["data"]["target"] for e in edges}
        sources = {e["data"]["source"] for e in edges}
        for node_data in nodes_data:
            code = node_data["id"]
            dept = code.split()[0] if " " in code else code
            node_data["department"] = dept
            if code not in targets:
                node_data["is_root"] = True
            if code not in sources:
                node_data["is_leaf"] = True

        nodes = [{"data": node_data} for node_data in nodes_data]

    return {"nodes": nodes, "edges": edges, "program_name": program_name}


def _get_required_codes(conn, poid: str) -> set[str]:
    """Get distinct required course codes for a program."""
    rows = conn.execute(
        text(
            "SELECT DISTINCT course_code FROM program_required_courses WHERE poid = :p"
        ),
        {"p": poid},
    ).fetchall()
    return {r[0] for r in rows if r[0]}


def _map_codes_to_coids(conn, codes: set[str]) -> dict[str, str]:
    """Map course codes to COIDs via `courses.course_code` column matching."""
    mapping = {}
    for code in codes:
        row = conn.execute(
            text("SELECT coid FROM courses WHERE course_code = :c LIMIT 1"),
            {"c": code},
        ).fetchone()
        if row:
            mapping[code] = row[0]
        else:
            logger.warning("No coid found for course_code=%s", code)
    return mapping


def _build_filtered_edges(
    conn, code_to_coid: dict, coid_to_code: dict, required_codes: set[str]
) -> list[dict]:
    """Build prerequisite edges, filtered to only required courses."""
    edges = []
    seen = set()

    for code, coid in code_to_coid.items():
        # Get all prereqs for this course
        prereqs = conn.execute(
            text(
                "SELECT prerequisite_coid "
                "FROM course_prerequisites "
                "WHERE course_coid = :c"
            ),
            {"c": coid},
        ).fetchall()

        for (prereq_coid,) in prereqs:
            prereq_code = coid_to_code.get(prereq_coid)

            # If prereq_coid isn't in our map, try looking it up
            if not prereq_code:
                prereq_code_row = conn.execute(
                    text("SELECT course_code FROM courses WHERE coid = :c"),
                    {"c": str(prereq_coid)},
                ).fetchone()
                if prereq_code_row:
                    prereq_code = prereq_code_row[0]

            # Only include edge if prereq is also in the required set
            if prereq_code and prereq_code in required_codes:
                edge_key = (prereq_code, code)
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append(
                        {
                            "data": {
                                "source": prereq_code,
                                "target": code,
                            }
                        }
                    )

    return edges


def _extract_course_code(course_name: str | None) -> str | None:
    """Extract course code from `COURSE CODE - Title` format."""
    if not course_name:
        return None
    # Use the same logic as fix_db_codes.py for consistency
    import re
    match = re.split(r'\s+[-–—:]\s+|\s+[-–—:]|\xa0[-–—:]\xa0', course_name)
    if match:
        return match[0].strip()
    return course_name.strip()
