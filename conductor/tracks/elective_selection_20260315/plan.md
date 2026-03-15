# Implementation Plan: Elective Selection and Course Tree Integration

## Phase 1: Backend API Consolidation and Expansion [checkpoint: 62c87ce]
*Objective: Ensure all necessary data is available through the FastAPI backend.*

- [x] Task: Backend - Programs List Endpoint d649bc6
    - [x] Write failing test for `GET /api/programs` in `server/tests/test_api.py`.
    - [x] Implement the `/api/programs` endpoint in `server/main.py`.
    - [x] Verify test passes and coverage is maintained.
- [x] Task: Backend - Course Detail Endpoint d649bc6
    - [x] Write failing test for `GET /api/course/{course_code}` in `server/tests/test_api.py`.
    - [x] Implement the `/api/course/{course_code}` endpoint in `server/main.py`.
    - [x] Verify test passes and coverage is maintained.
- [x] Task: Conductor - User Manual Verification 'Backend API Consolidation and Expansion' (Protocol in workflow.md) f3aca2d

## Phase 2: Frontend Component Refactoring [checkpoint: b04059f]
*Objective: Create the necessary UI components for major selection and elective exploration.*

- [x] Task: Frontend - Dynamic Major Selection 417eb84
    - [x] Write failing test for `MajorDropdown.tsx` to ensure it fetches from `/api/programs`.
    - [x] Update `MajorDropdown.tsx` to fetch and render dynamic options.
    - [x] Verify test passes and styling matches guidelines.
- [x] Task: Frontend - Accordion Elective List 78640cd
    - [x] Write failing test for `ElectiveList.tsx` accordion behavior and on-demand fetching.
    - [x] Refactor `ElectiveList.tsx` into an accordion with `ElectiveCourseItem` sub-components.
    - [x] Verify test passes and smooth transitions are implemented.
- [x] Task: Conductor - User Manual Verification 'Frontend Component Refactoring' (Protocol in workflow.md) b04059f

## Phase 3: Integration and Visualization [checkpoint: 0d9bb4b]
*Objective: Connect the frontend components and enhance the course tree visualization.*

- [x] Task: Frontend - Global State Management b6f40a9
    - [x] Write failing test for `App.tsx` ensuring `poid` state updates correctly.
    - [x] Update `App.tsx` to manage selected major and pass it to `CourseTree`.
    - [x] Verify test passes.
- [x] Task: Frontend - Course Tree Department Filtering 72c8d6f
    - [x] Write failing test for department filtering in `CourseTree.tsx`.
    - [x] Implement multi-select filter for departments in `CourseTree.tsx`.
    - [x] Verify test passes and graph updates correctly.
- [x] Task: Conductor - User Manual Verification 'Integration and Visualization' (Protocol in workflow.md) 0d9bb4b
