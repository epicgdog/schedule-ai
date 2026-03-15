# Implementation Plan: Fix Server & Major Tree Generation

## Objective
Fix the broken FastAPI server and connect the frontend to allow generating a prerequisite tree for every available major.

## Project Architecture Notes
- **Backend:** FastAPI, Python, SQLAlchemy (SQLite/Turso via libsql). The entry point is `server/main.py`.
- **Frontend:** React, Vite, TypeScript, Tailwind CSS. Uses Cytoscape.js and Dagre for visualizing interactive graphs.
- **Data Pipeline:** Python scrapers and DB loaders residing in `sjsu-data-retrival/` (populate course info, pre-requisites, GE areas, and program requirements into an SQLite DB).

## Proposed Solution
1. **Fix Backend Error:** Remove the duplicated `/api/course_tree/{poid}` endpoint in `server/main.py` that incorrectly shadows the working endpoint and alters the response format.
2. **Fetch Available Majors:** Add a `/api/programs` endpoint in `server/main.py` that queries the database for `poid` and `program_name`.
3. **Dynamic Frontend Selection:** Update `MajorDropdown.tsx` to fetch the real list of majors and their POIDs from the backend, instead of using hardcoded string values.
4. **App State Integration:** Update `App.tsx` to hold the selected `poid` state from the dropdown, and pass it to `<CourseTree />` so a user can see the prerequisite tree for any available major.
5. **Context7 MCP:** I will use the Context7 MCP tools (`mcp_context7_resolve-library-id` and `mcp_context7_query-docs`) to look up React, FastAPI, or Cytoscape.js documentation as needed during implementation.

## Implementation Steps
- [x] Fix `server/main.py`: Remove the duplicate `@app.get("/api/course_tree/{poid}")` function at the end of the file.
- [x] Add `/api/programs` endpoint to `server/main.py` that queries the `programs` table for all available programs.
- [x] Update `MajorDropdown.tsx` to fetch from `/api/programs` and render the fetched options as `<select>` choices.
- [x] Update `App.tsx` to use `useState` for the selected `poid` and wire it up to `MajorDropdown` and `CourseTree`.
- [x] Fix database mapping: Populated `course_code` column in `courses` table and updated `course_tree.py` to use it for matching.
- [x] Add department filtering to `CourseTree.tsx`: Implement a multi-select filter to show/hide courses based on their department (CS, MATH, etc.).


## Verification
- Start the backend server and ensure it launches without errors.
- Run the React frontend and test that the dropdown displays the real list of SJSU majors.
- Select different majors and verify that the prerequisite tree graph dynamically updates for each major.
