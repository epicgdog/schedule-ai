# Implementation Plan: ElectiveList Accordion & Course Descriptions

## Objective
Enhance the `ElectiveList` component by converting it into an accordion-style interface where each elective group can be expanded/collapsed. Additionally, allow users to see course descriptions for individual elective choices through nested dropdowns/toggles.

## Proposed Changes

### Backend (`server/main.py`)
- [x] Add a new endpoint `@app.get("/api/course/{course_code}")` that returns the `course_name` and `description` for a given course code. This will be used to fetch descriptions on-demand when a user expands a course in the elective list.

### Frontend (`frontend/src/components/ElectiveList.tsx`)
- [x] **State Management:** Add state to track which elective group is currently expanded (Accordion behavior).
- [x] **Accordion UI:** Wrap each elective group in a collapsible container with a toggle header.
- [x] **Course Item Component:** Create a sub-component for elective course items that:
    - Displays the course code as a button/toggle.
    - On click, fetches the course description from the new backend endpoint.
    - Displays the fetched description in a nested collapsible area (Dropdown/Tooltip style).
- [x] **Styling:** Use Tailwind CSS for smooth transitions and SJSU-themed styling.

## Implementation Steps
1.  **Backend Endpoint:**
    - Modify `server/main.py` to add the `/api/course/{course_code}` endpoint.
    - Query the `courses` table using the `course_code` column.
2.  **Frontend Component Update:**
    - Update `ElectiveList.tsx` with accordion logic for groups.
    - Implement a nested `ElectiveCourseItem` component within `ElectiveList.tsx` to handle on-demand description fetching and display.
3.  **Verification:**
    - Test selecting a major and ensuring the "Program Electives" section appears.
    - Test expanding/collapsing elective groups.
    - Test clicking a course code to see its description and verify the backend call.

## Verification
- Verify that clicking an elective group header toggles its visibility.
- Verify that clicking a course badge within a group fetches and displays the correct description.
- Ensure only one elective group is expanded at a time (standard accordion) or allow multiple (flexible accordion) based on UX preference (standard preferred).
