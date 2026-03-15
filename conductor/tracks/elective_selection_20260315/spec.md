# Specification: Elective Selection and Course Tree Integration

## Overview
This track focuses on enhancing the user experience for SJSU students by providing a more intuitive interface for selecting elective courses and visualizing their entire program's prerequisite tree. This involves refactoring the existing elective list into an accordion-style component, integrating it with a dynamic course tree visualization, and ensuring all data is fetched from a unified backend.

## Functional Requirements

### Backend API
- **Course Detail Endpoint:** `GET /api/course/{course_code}` should return the full description and name of a course.
- **Programs List Endpoint:** `GET /api/programs` should return a list of all available academic programs (POIDs) and their names.
- **Tree Generation Endpoint:** `GET /api/course_tree/{poid}` (already exists) should be robust and return the prerequisite structure for the selected program.

### Frontend Components
- **Major Selection:** `MajorDropdown.tsx` must fetch its options dynamically from `/api/programs`.
- **Elective Selection:** `ElectiveList.tsx` should be an accordion-style component where students can expand/collapse elective groups and see individual course descriptions on-demand.
- **Visualization:** `CourseTree.tsx` must render the prerequisite tree for the selected major using Cytoscape.js and include department-based filtering.
- **App Integration:** `App.tsx` must manage the global state for the selected major and ensure all components update accordingly.

## Non-Functional Requirements
- **Performance:** On-demand fetching of course descriptions to minimize initial load time.
- **UI/UX:** Adhere to the "Modern High-Contrast" palette and "Academic and Direct" tone defined in the product guidelines.
- **Maintainability:** Follow the TDD workflow with >80% code coverage.

## Acceptance Criteria
- [ ] Users can select any available major from a dropdown and see its prerequisite tree.
- [ ] Prerequisite trees are correctly rendered and can be filtered by department.
- [ ] The elective list is presented as a clean accordion, and clicking a course reveals its description.
- [ ] All data is fetched from the backend on-demand.
- [ ] All unit and integration tests pass with high coverage.

## Out of Scope
- User authentication and personalized schedule saving (to be handled in a later track).
- Course scheduling algorithm (finding open sections based on time constraints).
