# Specification: Hybrid View Persistence & Dynamic Progress Tracking

## Overview
Ensure a seamless planning experience where data is cached, UI state is preserved, and progress visualization (completed vs. needed courses) updates instantly when new academic records are uploaded.

## Functional Requirements

### 1. Global Data Caching (PlannerContext)
- **Centralized Storage:** `CourseTree` and `ElectiveList` data stored in `PlannerContext.tsx`.
- **Session Persistence:** Cache persists across refreshes via `localStorage`.

### 2. UI State Persistence (CSS-based)
- **Component Lifecycle:** Components for each tab remain mounted. Use CSS visibility/display to switch views.
- **Goal:** Preserve Cytoscape zoom/pan and user interaction state.

### 3. Reactive Progress Visualization
- **Instant Tree Updates:** When `courseHistory` (transcript) is updated in the context:
    - `CourseTree` must immediately re-calculate node styling to clearly show what the student has **already taken**, what they **need to take** (Available, prereqs met), and what is **locked**.
    - No re-fetch of the graph structure should be required; only a re-render of the existing nodes.
- **Instant Elective Updates:** 
    - `ElectiveList` must react to the `courseHistory` to show which electives have been completed.
    - Accurately track remaining elective requirements (what they still need to take to fulfill the group).
- **Visual Feedback:** Use distinct glassmorphism styles (e.g., green glows for completed, dimmed opacity for locked) to differentiate course status across both Tree and Elective views.

## Acceptance Criteria
- [ ] Uploading a transcript instantly updates the completion status of nodes on the currently visible tree.
- [ ] Switching between "Academic Tree" and other tabs preserves the exact graph position.
- [ ] Data for previously visited majors persists across sessions.

## Out of Scope
- Manual override of course status (must be done via transcript upload for now).