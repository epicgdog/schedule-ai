# Implementation Plan: Hybrid View Persistence & Dynamic Progress Tracking

## Phase 1: Context-Based Caching & Persistence [checkpoint: f221557]
*Objective: Centralize data fetching and enable cross-session persistence.*

- [x] Task: Frontend - Cache State in PlannerContext 547e463
    - [x] Update `PlannerContext.tsx` to include `treeCache` and `electiveCache`.
    - [x] Implement `loadMajorData(poid)` action in context that handles caching and fetching.
- [x] Task: Frontend - LocalStorage Persistence 01eb88c
    - [x] Implement `useEffect` in `PlannerContext` to sync cache to `localStorage`.
    - [x] Implement hydration logic to load cache on startup.
- [x] Task: Conductor - User Manual Verification 'Context-Based Caching & Persistence' (Protocol in workflow.md) f221557

## Phase 2: Persistent Dashboard Layout [checkpoint: c5ab48e]
*Objective: Prevent component unmounting to preserve UI state (zoom/pan).*

- [x] Task: Frontend - CSS-based Tab Switching d9d2057
    - [x] Refactor `App.tsx` to render all tab components simultaneously.
    - [x] Use Tailwind `hidden` class or `display: none` based on `activeTab`.
- [x] Task: Frontend - Component Refactor for Context Data 4ee93a6
    - [x] Update `CourseTree.tsx` to consume data from `PlannerContext` instead of fetching internally.
    - [x] Update `ElectiveList.tsx` to consume data from `PlannerContext`.
- [x] Task: Conductor - User Manual Verification 'Persistent Dashboard Layout' (Protocol in workflow.md) c5ab48e

## Phase 3: Reactive Progress Visualization
*Objective: Ensure the tree and elective lists react instantly to transcript uploads.*

- [ ] Task: Frontend - Reactive Node Styling (Course Tree)
    - [ ] Update `CourseTree.tsx` to watch `courseHistory` and dynamically calculate node states (Completed, Available, Locked).
    - [ ] Refine visual styles in Cytoscape for "Completed", "Available" (need to take), and "Locked" nodes without re-initializing the graph.
- [ ] Task: Frontend - Reactive Elective Tracking
    - [ ] Update `ElectiveList.tsx` to evaluate `courseHistory` against available choices.
    - [ ] Add visual indicators for completed electives (e.g., checked off, green text).
    - [ ] Update requirement logic to clearly indicate how many choices are still needed.
- [ ] Task: Frontend - Polish & Cleanup
    - [ ] Ensure `TranscriptUploader` correctly triggers the global state update for both components.
    - [ ] Remove redundant `useEffect` hooks and local states from components.
- [ ] Task: Conductor - User Manual Verification 'Reactive Progress Visualization' (Protocol in workflow.md)