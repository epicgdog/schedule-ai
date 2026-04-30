"""
Pre-build course tree JSON for all programs.

This standalone script:
1. Creates the program_trees table if it doesn't exist
2. Iterates through all programs in the database
3. Builds their prerequisite trees (via build_course_tree)
4. Fetches electives
5. Stores the combined JSON in the program_trees table for fast serving

Usage:
    python build_trees.py              # Build all trees
    python build_trees.py --poid 13772  # Build single program
    python build_trees.py --rebuild     # Clear and rebuild all trees
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "server"))
sys.path.insert(0, str(PROJECT_ROOT / "sjsu-data-retrival"))

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import text

from db import get_engine, Base, ProgramTree
from sqlalchemy.orm import Session


def ensure_table_exists(engine) -> None:
    """Create program_trees table if it doesn't exist."""
    Base.metadata.create_all(engine)
    logger.info("Ensured program_trees table exists")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_trees(poid: str | None = None, rebuild: bool = False) -> None:
    """Build and store pre-computed trees for all programs (or a single poid)."""
    engine = get_engine()

    ensure_table_exists(engine)

    if rebuild:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM program_trees"))
            conn.commit()
        logger.info("Cleared existing trees")

    with engine.connect() as conn:
        if poid:
            programs = conn.execute(
                text("SELECT poid, program_name FROM programs WHERE poid = :p"),
                {"p": poid},
            ).fetchall()
            if not programs:
                logger.error(f"No program found with poid={poid}")
                return
        else:
            programs = conn.execute(
                text("SELECT poid, program_name FROM programs ORDER BY program_name")
            ).fetchall()

    if not programs:
        logger.warning("No programs found in database")
        return

    logger.info(f"Building trees for {len(programs)} program(s)")

    from course_tree import build_course_tree

    success_count = 0
    error_count = 0

    for poid_val, program_name in programs:
        try:
            logger.info(f"  Building tree for {program_name} ({poid_val})...")

            tree_data = build_course_tree(engine, poid_val)

            with engine.connect() as conn:
                electives_rows = conn.execute(
                    text(
                        "SELECT heading, instructions, choices_json FROM program_elective_groups WHERE poid = :p"
                    ),
                    {"p": poid_val},
                ).fetchall()

            electives = [
                {
                    "heading": r[0],
                    "instructions": r[1],
                    "choices": json.loads(r[2]) if r[2] else [],
                }
                for r in electives_rows
            ]

            combined = {
                "nodes": tree_data.get("nodes", []),
                "edges": tree_data.get("edges", []),
                "program_name": tree_data.get("program_name"),
                "electives": electives,
            }

            tree_json = json.dumps(combined)

            with Session(engine) as session:
                existing = session.get(ProgramTree, poid_val)
                if existing:
                    existing.tree_json = tree_json
                    existing.generated_at = datetime.now(timezone.utc).isoformat()
                else:
                    program_tree = ProgramTree(
                        poid=poid_val,
                        tree_json=tree_json,
                        generated_at=datetime.now(timezone.utc).isoformat(),
                    )
                    session.add(program_tree)
                session.commit()

            success_count += 1
            logger.info(
                f"    ✓ {len(tree_data.get('nodes', []))} nodes, {len(tree_data.get('edges', []))} edges, {len(electives)} elective groups"
            )

        except Exception as e:
            error_count += 1
            logger.exception(f"    ✗ Failed to build tree for {poid_val}: {e}")

    logger.info(f"Done: {success_count} succeeded, {error_count} failed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-build course trees for all programs"
    )
    parser.add_argument(
        "--poid",
        type=str,
        default=None,
        help="Build tree for a specific poid only",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Clear existing trees before building",
    )
    args = parser.parse_args()

    build_trees(args.poid, args.rebuild)


if __name__ == "__main__":
    main()
