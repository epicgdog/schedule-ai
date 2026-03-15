"""
Shared database module — SQLAlchemy engine + ORM models for Turso/SQLite.

Uses `libsql` with a connection wrapper since `sqlalchemy-libsql` does not
support Windows.  Falls back to local SQLite when Turso env vars are absent.

Usage:
    from db import get_engine, Base, Course, CoursePrerequisite, CourseCorequisite

    engine = get_engine()
    Base.metadata.create_all(engine)
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

# ── Environment ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)


# ── libsql wrapper (Windows-compatible) ──────────────────────────
class _LibSQLConnectionWrapper:
    """Thin wrapper around a ``libsql`` connection.

    SQLAlchemy's SQLite dialect calls ``create_function`` on new connections.
    ``libsql`` connections don't support that, so we silently swallow the call.
    """

    def __init__(self, conn):
        self._conn = conn

    def create_function(self, *args, **kwargs):
        pass  # SQLAlchemy compat shim

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_engine():
    """Create a SQLAlchemy engine, preferring Turso if configured."""
    turso_url = os.getenv("TURSO_DATABASE_URL")
    turso_token = os.getenv("TURSO_ACCESS_TOKEN")

    if turso_url and turso_token:
        try:
            import libsql

            def _creator():
                conn = libsql.connect(database=turso_url, auth_token=turso_token)
                return _LibSQLConnectionWrapper(conn)

            logger.info("Connecting to Turso: %s", turso_url)
            return create_engine("sqlite://", creator=_creator)
        except ImportError:
            logger.warning("libsql not installed — falling back to local SQLite")

    db_path = str(PROJECT_ROOT / os.getenv("DATABASE", "sjsu-data-retrival/sjsu_courses.db"))
    logger.info("Using local SQLite: %s", db_path)
    return create_engine(f"sqlite:///{db_path}")


# ── ORM Base ─────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Models ───────────────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"

    coid = Column(String, primary_key=True)
    course_name = Column(String, nullable=False)
    description = Column(Text)
    units = Column(String)
    ge_area = Column(String)
    prerequisites_text = Column(Text)
    corequisites_text = Column(Text)

    prerequisites = relationship(
        "CoursePrerequisite",
        foreign_keys="CoursePrerequisite.course_coid",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    corequisites = relationship(
        "CourseCorequisite",
        foreign_keys="CourseCorequisite.course_coid",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course coid={self.coid!r} name={self.course_name!r}>"


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (
        UniqueConstraint("course_coid", "prerequisite_coid", name="uq_prereq"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_coid = Column(String, ForeignKey("courses.coid"), nullable=False)
    prerequisite_coid = Column(String, nullable=False)

    course = relationship(
        "Course",
        foreign_keys=[course_coid],
        back_populates="prerequisites",
    )

    def __repr__(self) -> str:
        return f"<Prereq {self.course_coid!r} -> {self.prerequisite_coid!r}>"


class CourseCorequisite(Base):
    __tablename__ = "course_corequisites"
    __table_args__ = (
        UniqueConstraint("course_coid", "corequisite_coid", name="uq_coreq"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_coid = Column(String, ForeignKey("courses.coid"), nullable=False)
    corequisite_coid = Column(String, nullable=False)

    course = relationship(
        "Course",
        foreign_keys=[course_coid],
        back_populates="corequisites",
    )

    def __repr__(self) -> str:
        return f"<Coreq {self.course_coid!r} -> {self.corequisite_coid!r}>"


# ── Program Requirements Models ──────────────────────────────────


class ProgramRequiredCourse(Base):
    """A required course for a specific program (major)."""

    __tablename__ = "program_required_courses"
    __table_args__ = (
        UniqueConstraint("poid", "course_code", name="uq_prog_req_course"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    poid = Column(String, nullable=False)
    course_code = Column(String, nullable=False)  # e.g. "CS 46A"

    def __repr__(self) -> str:
        return f"<ProgReq poid={self.poid!r} course={self.course_code!r}>"


class ProgramElectiveGroup(Base):
    """An elective group within a program's requirements."""

    __tablename__ = "program_elective_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poid = Column(String, nullable=False)
    heading = Column(String, nullable=False)
    instructions = Column(String)
    choices_json = Column(Text)  # JSON array of course codes, e.g. '["CS 116A","CS 116B"]'

    def __repr__(self) -> str:
        return f"<ElectiveGroup poid={self.poid!r} heading={self.heading!r}>"
