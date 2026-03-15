# Implementation Plan: UI/UX Overhaul - Unified Glassmorphism Dashboard

## Phase 1: Dashboard Scaffolding & Glassmorphism Theme [checkpoint: 1c005a5]
*Objective: Establish the new layout and visual baseline.*

- [x] Task: Frontend - Glassmorphism UI Components 91e6a75
    - [x] Create `GlassPanel.tsx` and `GlassButton.tsx` primitive components with backdrop-blur and transparency.
    - [x] Define global CSS variables for glassmorphism colors in `index.css`.
- [x] Task: Frontend - Sidebar Navigation 665b4fe
    - [x] Write failing test for `Sidebar.tsx` ensuring it switches active views.
    - [x] Implement `Sidebar.tsx` with icons for Tree, GE, and Schedule.
    - [x] Verify test passes and layout is fixed-width on desktop.
- [x] Task: Frontend - Dashboard Layout Integration 6a4df6b
    - [x] Write failing test for `DashboardLayout.tsx` ensuring it renders children and sidebar correctly.
    - [x] Refactor `App.tsx` to use `DashboardLayout`.
    - [x] Verify test passes.
- [x] Task: Conductor - User Manual Verification 'Dashboard Scaffolding & Glassmorphism Theme' (Protocol in workflow.md) 1c005a5

## Phase 2: Global State & Transcript Processing [checkpoint: b49aae9]
*Objective: Centralize state and enable personalized progress tracking.*

- [x] Task: Frontend - Global State Management 803a6d9
    - [x] Setup React Context (or similar) to manage: `selectedMajor`, `courseHistory`, and `plannedCourses`.
    - [x] Refactor existing components to use global state instead of local prop drilling.
- [x] Task: Frontend - Transcript Upload Integration 6049986
    - [x] Write failing test for `TranscriptUploader.tsx` (wrapping `CourseInput` logic).
    - [x] Integrate the uploader into the Sidebar or Header.
    - [x] Verify that uploaded courses update the global `courseHistory` state.
- [x] Task: Conductor - User Manual Verification 'Global State & Transcript Processing' (Protocol in workflow.md) b49aae9

## Phase 3: Component Overhaul (Tree & GE) [checkpoint: 0af4213]
*Objective: Update primary views with new styles and completion status logic.*

- [x] Task: Frontend - Enhanced CourseTree 602c6ad
    - [x] Update `CourseTree.tsx` to accept `courseHistory` and highlight completed nodes.
    - [x] Apply glassmorphism styles to the floating filter panel.
    - [x] Verify node highlighting logic via unit tests.
- [x] Task: Frontend - Enhanced GeTracker 126ae53
    - [x] Refactor `GeTracker.tsx` to use the new glassmorphism panels.
    - [x] Ensure progress bars and status badges are updated based on global `courseHistory`.
    - [x] Verify layout responsiveness.
- [x] Task: Conductor - User Manual Verification 'Component Overhaul (Tree & GE)' (Protocol in workflow.md) 0af4213

## Phase 4: Interaction Layer & Polish [checkpoint: d18a7be]
*Objective: Finalize the interactive experience and visual details.*

- [x] Task: Frontend - Course Detail Modal 5bc5a5a
    - [x] Write failing test for `CourseDetailModal.tsx`.
    - [x] Implement the modal with support for description, units, and `ElectiveList`.
    - [x] Connect `CourseTree` node clicks to trigger this modal.
- [x] Task: Frontend - Animation & Polish e37e57c
    - [x] Add `framer-motion` (or similar) for view transitions.
    - [x] Implement skeleton loaders for graph and elective data fetching.
    - [x] Final visual pass for spacing and consistency.
- [x] Task: Conductor - User Manual Verification 'Interaction Layer & Polish' (Protocol in workflow.md) d18a7be
