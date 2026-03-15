# Implementation Plan: UI/UX Overhaul - Unified Glassmorphism Dashboard

## Phase 1: Dashboard Scaffolding & Glassmorphism Theme
*Objective: Establish the new layout and visual baseline.*

- [ ] Task: Frontend - Glassmorphism UI Components
    - [ ] Create `GlassPanel.tsx` and `GlassButton.tsx` primitive components with backdrop-blur and transparency.
    - [ ] Define global CSS variables for glassmorphism colors in `index.css`.
- [ ] Task: Frontend - Sidebar Navigation
    - [ ] Write failing test for `Sidebar.tsx` ensuring it switches active views.
    - [ ] Implement `Sidebar.tsx` with icons for Tree, GE, and Schedule.
    - [ ] Verify test passes and layout is fixed-width on desktop.
- [ ] Task: Frontend - Dashboard Layout Integration
    - [ ] Write failing test for `DashboardLayout.tsx` ensuring it renders children and sidebar correctly.
    - [ ] Refactor `App.tsx` to use `DashboardLayout`.
    - [ ] Verify test passes.
- [ ] Task: Conductor - User Manual Verification 'Dashboard Scaffolding & Glassmorphism Theme' (Protocol in workflow.md)

## Phase 2: Global State & Transcript Processing
*Objective: Centralize state and enable personalized progress tracking.*

- [ ] Task: Frontend - Global State Management
    - [ ] Setup React Context (or similar) to manage: `selectedMajor`, `courseHistory`, and `plannedCourses`.
    - [ ] Refactor existing components to use global state instead of local prop drilling.
- [ ] Task: Frontend - Transcript Upload Integration
    - [ ] Write failing test for `TranscriptUploader.tsx` (wrapping `CourseInput` logic).
    - [ ] Integrate the uploader into the Sidebar or Header.
    - [ ] Verify that uploaded courses update the global `courseHistory` state.
- [ ] Task: Conductor - User Manual Verification 'Global State & Transcript Processing' (Protocol in workflow.md)

## Phase 3: Component Overhaul (Tree & GE)
*Objective: Update primary views with new styles and completion status logic.*

- [ ] Task: Frontend - Enhanced CourseTree
    - [ ] Update `CourseTree.tsx` to accept `courseHistory` and highlight completed nodes.
    - [ ] Apply glassmorphism styles to the floating filter panel.
    - [ ] Verify node highlighting logic via unit tests.
- [ ] Task: Frontend - Enhanced GeTracker
    - [ ] Refactor `GeTracker.tsx` to use the new glassmorphism panels.
    - [ ] Ensure progress bars and status badges are updated based on global `courseHistory`.
    - [ ] Verify layout responsiveness.
- [ ] Task: Conductor - User Manual Verification 'Component Overhaul (Tree & GE)' (Protocol in workflow.md)

## Phase 4: Interaction Layer & Polish
*Objective: Finalize the interactive experience and visual details.*

- [ ] Task: Frontend - Course Detail Modal
    - [ ] Write failing test for `CourseDetailModal.tsx`.
    - [ ] Implement the modal with support for description, units, and `ElectiveList`.
    - [ ] Connect `CourseTree` node clicks to trigger this modal.
- [ ] Task: Frontend - Animation & Polish
    - [ ] Add `framer-motion` (or similar) for view transitions.
    - [ ] Implement skeleton loaders for graph and elective data fetching.
    - [ ] Final visual pass for spacing and consistency.
- [ ] Task: Conductor - User Manual Verification 'Interaction Layer & Polish' (Protocol in workflow.md)
