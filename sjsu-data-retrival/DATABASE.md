# SJSU Schedule AI Database

This document describes the database schema for the SJSU Schedule AI project. The database can run either locally (SQLite) or in the cloud (Turso).

## Connection

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE` | Yes | Path to SQLite database (e.g., `db/main.db`) |
| `TURSO_DATABASE_URL` | No | Turso libsql URL (e.g., `libsql://your-db.turso.io`) |
| `TURSO_ACCESS_TOKEN` | No | Turso authentication token |

### How It Works

The `get_engine()` function in `db.py` checks for Turso credentials:
- If `TURSO_DATABASE_URL` and `TURSO_ACCESS_TOKEN` are set → connects to Turso
- Otherwise → uses local SQLite via the `DATABASE` path

```python
# sjsu-data-retrival/db.py
def get_engine():
    turso_url = os.getenv("TURSO_DATABASE_URL")
    turso_token = os.getenv("TURSO_ACCESS_TOKEN")
    
    if turso_url and turso_token:
        # Connect to Turso
        return create_engine("sqlite://", creator=_creator)
    
    # Fall back to local SQLite
    return create_engine(f"sqlite:///{db_path}")
```

---

## Tables

### 1. courses

Course catalog information from SJSU.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `coid` | TEXT | PRIMARY KEY | Catalog Object ID (e.g., `"159178"`) |
| `course_name` | TEXT | NOT NULL | Full name (e.g., `"CS 146 - Data Structures & Algorithms"`) |
| `description` | TEXT | | Course description |
| `units` | TEXT | | Credit units (e.g., `"3"`) |
| `ge_area` | TEXT | | GE area satisfaction text |
| `prerequisites_text` | TEXT | | Human-readable prereq text |
| `corequisites_text` | TEXT | | Human-readable coreq text |

**Source:** Populated by `course_detail_scraper.py` (scrapes catalog.sjsu.edu)

---

### 2. course_prerequisites

Prerequisite relationships between courses. Each row is a directed edge: "course X requires course Y".

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `course_coid` | TEXT | FK → courses.coid | The course that has the prerequisite |
| `prerequisite_coid` | TEXT | NOT NULL | COID of the prerequisite course |

**Unique Constraint:** `(course_coid, prerequisite_coid)`

**Note:** Both COIDs are internal catalog IDs, not human-readable codes. Join with `courses` table to get course codes.

---

### 3. course_corequisites

Corequisite relationships (courses that must be taken together).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `course_coid` | TEXT | FK → courses.coid | The course with the corequisite |
| `corequisite_coid` | TEXT | NOT NULL | COID of the corequisite course |

**Unique Constraint:** `(course_coid, corequisite_coid)`

---

### 4. programs

All degree programs/majors at SJSU.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `poid` | TEXT | | Program Object ID from catalog |
| `program_name` | TEXT | | Program name (e.g., `"Computer Science, BS"`) |
| `requirements_json` | TEXT | | Raw LLM-extracted JSON (optional) |

**Source:** Populated by `major_loader.py`

---

### 5. program_required_courses

Required courses for each program. Each row = one required course.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `poid` | TEXT | NOT NULL | Program Object ID |
| `course_code` | TEXT | NOT NULL | Course code (e.g., `"CS 46A"`) |

**Unique Constraint:** `(poid, course_code)`

**Source:** Populated by `program_requirements_scraper.py` using Groq LLM

---

### 6. program_elective_groups

Elective course groups within a program.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `poid` | TEXT | NOT NULL | Program Object ID |
| `heading` | TEXT | NOT NULL | Group heading (e.g., `"Technical Electives"`) |
| `instructions` | TEXT | | Instructions text |
| `choices_json` | TEXT | | JSON array of course codes |

**Example:**
```json
["CS 116A", "CS 116B", "CS 116C"]
```

**Source:** Populated by `program_requirements_scraper.py`

---

### 7. program_trees

**Pre-computed prerequisite trees** for fast rendering. Generated once and served directly.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `poid` | TEXT | PRIMARY KEY | Program Object ID |
| `tree_json` | TEXT | NOT NULL | Combined tree + electives JSON |
| `generated_at` | TEXT | NOT NULL | ISO timestamp of generation |

**JSON Structure:**
```json
{
  "nodes": [{"data": {"id": "CS 46A", "label": "CS 46A", "department": "CS", "is_root": true}}],
  "edges": [{"data": {"source": "MATH 30", "target": "CS 46A"}}],
  "program_name": "Computer Science, BS",
  "electives": [{"heading": "...", "instructions": "...", "choices": ["CS 116A"]}]
}
```

**Generation:** Run `python sjsu-data-retrival/build_trees.py`

---

### 8. ge_courses

General Education (GE) courses by area.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `area` | TEXT | NOT NULL | GE sub-area (e.g., `"A1"`, `"B3"`) |
| `code` | TEXT | NOT NULL | Course code (e.g., `"COMM 20"`) |
| `title` | TEXT | NOT NULL | Course title |
| `us1` | INTEGER | | Satisfies US1 flag |
| `us2` | INTEGER | | Satisfies US2 flag |
| `us3` | INTEGER | | Satisfies US3 flag |
| `lab_credit` | INTEGER | | Lab credit flag |

**Unique Constraint:** `(area, code, title)`

**Source:** Populated by `ge_loader.py` (scrapes catalog.sjsu.edu)

---

### 9. major_ge_exceptions

GE area waivers/exceptions for specific majors.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `major` | TEXT | NOT NULL | Major name (e.g., `"Software Engineering"`) |
| `degree` | TEXT | NOT NULL | Degree type (e.g., `"BS"`) |
| `waived_ge_areas` | TEXT | NOT NULL | JSON of waived areas |
| `notes` | TEXT | | Explanation text |
| `catalog_year` | TEXT | DEFAULT `'2021-2022'` | Catalog year |

**Unique Constraint:** `(major, degree, catalog_year)`

**Example `waived_ge_areas`:**
```json
{"UPPER": {"Areas": ["S", "V"], "Units": 6}, "PE": {"Areas": ["PE"], "Units": 2}}
```

---

### 10. sjsu_classes

Current semester class sections (live schedule).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `course_name` | TEXT | NOT NULL | Course code (e.g., `"CS 46A"`) |
| `section_number` | INTEGER | NOT NULL | Section number |
| `class_number` | INTEGER | NOT NULL UNIQUE | Class CRN |
| `days` | TEXT | | Days meeting (e.g., `"MW"`) |
| `start_time` | TEXT | | Start time (e.g., `"10:30AM"`) |
| `end_time` | TEXT | | End time (e.g., `"11:45AM"`) |
| `instructor` | TEXT | | Instructor name |
| `open_seats` | INTEGER | NOT NULL | Available seats |

**Source:** Populated by `current_course_loader.py` (scrapes class schedule)

---

### 11. reqs

Legacy table for program requirements (superseded by `programs` + `program_required_courses`).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `course_name` | TEXT | NOT NULL, UNIQUE | Program name |
| `description` | TEXT | | JSON blob of requirements |

---

## Development Commands

### Build Database

```bash
# Build all tables (run from project root)
python sjsu-data-retrival/build_db.py

# Run specific loaders
python sjsu-data-retrival/build_db.py --only ge courses

# Force re-scrape everything
python sjsu-data-retrival/build_db.py --force
```

### Build Trees

```bash
# First time: create table and build all trees
python sjsu-data-retrival/build_trees.py

# Rebuild all trees (clears old data)
python sjsu-data-retrival/build_trees.py --rebuild

# Build just one program
python sjsu-data-retrival/build_trees.py --poid 13772
```

### Query Database Directly

```bash
# Using sqlite3 (local only)
sqlite3 db/main.db

# Example queries
sqlite> SELECT poid, program_name FROM programs LIMIT 5;
sqlite> SELECT COUNT(*) FROM courses;
sqlite> SELECT * FROM program_trees WHERE poid = '13772';
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SJSU Schedule AI                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + Cytoscape.js)                          │
│  └── /api/course_tree/{poid} → reads program_trees       │
│  └── /api/electives/{poid}    → reads program_trees      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  FastAPI Server (server/main.py)                           │
│  ├── modules.py      → DB queries, RateMyProfessors API   │
│  ├── agent.py        → LLM for GE analysis                │
│  └── course_tree.py → Build prerequisite graphs           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  Database (SQLite or Turso)                                │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │   courses    │ │course_prereqs│ │course_coreqs │     │
│  └──────────────┘ └──────────────┘ └──────────────┘     │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │   programs   │ │prog_required │ │prog_electives│     │
│  └──────────────┘ └──────────────┘ └──────────────┘     │
│                    └──────────────┘                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │program_trees │ │  ge_courses  │ │sjsu_classes  │     │
│  └──────────────┘ └──────────────┘ └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Notes

- `program_trees` is a **performance optimization** - the frontend expects the same JSON structure whether from cache or live-built
- Prerequisite edges in `course_prerequisites` are **flat** (no AND/OR logic) - the raw text in `courses.prerequisites_text` contains the actual logic
- Turso requires `libsql` Python package - falls back to local SQLite if not installed
