# Implementation Plan: Elective Selection and Course Tree Integration

## Phase 1: Backend API Consolidation and Expansion
*Objective: Ensure all necessary data is available through the FastAPI backend.*

- [x] Task: Backend - Programs List Endpoint d649bc6
    - [x] Write failing test for `GET /api/programs` in `server/tests/test_api.py`.
    - [x] Implement the `/api/programs` endpoint in `server/main.py`.
    - [x] Verify test passes and coverage is maintained.
- [x] Task: Backend - Course Detail Endpoint d649bc6
    - [x] Write failing test for `GET /api/course/{course_code}` in `server/tests/test_api.py`.
    - [x] Implement the `/api/course/{course_code}` endpoint in `server/main.py`.
    - [x] Verify test passes and coverage is maintained.
- [ ] Task: Conductor - User Manual Verification 'Backend API Consolidation and Expansion' (Protocol in workflow.md)

## Phase 2: Frontend Component Refactoring
*Objective: Create the necessary UI components for major selection and elective exploration.*

- [ ] Task: Frontend - Dynamic Major Selection
    - [ ] Write failing test for `MajorDropdown.tsx` to ensure it fetches from `/api/programs`.
    - [ ] Update `MajorDropdown.tsx` to fetch and render dynamic options.
    - [ ] Verify test passes and styling matches guidelines.
- [ ] Task: Frontend - Accordion Elective List
    - [ ] Write failing test for `ElectiveList.tsx` accordion behavior and on-demand fetching.
    - [ ] Refactor `ElectiveList.tsx` into an accordion with `ElectiveCourseItem` sub-components.
    - [ ] Verify test passes and smooth transitions are implemented.
- [ ] Task: Conductor - User Manual Verification 'Frontend Component Refactoring' (Protocol in workflow.md)

## Phase 3: Integration and Visualization
*Objective: Connect the frontend components and enhance the course tree visualization.*

- [ ] Task: Frontend - Global State Management
    - [ ] Write failing test for `App.tsx` ensuring `poid` state updates correctly.
    - [ ] Update `App.tsx` to manage selected major and pass it to `CourseTree`.
    - [ ] Verify test passes.
- [ ] Task: Frontend - Course Tree Department Filtering
    - [ ] Write failing test for department filtering in `CourseTree.tsx`.
    - [ ] Implement multi-select filter for departments in `CourseTree.tsx`.
    - [ ] Verify test passes and graph updates correctly.
- [ ] Task: Conductor - User Manual Verification 'Integration and Visualization' (Protocol in workflow.md)
