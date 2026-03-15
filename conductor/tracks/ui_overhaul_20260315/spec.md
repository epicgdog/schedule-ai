# Specification: UI/UX Overhaul - Unified Glassmorphism Dashboard

## Overview
Transform Schedule AI into a cohesive, dashboard-driven experience with a "Tree-Centric" interface. This overhaul includes a modern Glassmorphism aesthetic and integrates student course history to provide personalized planning and progress visualization.

## Functional Requirements

### 1. Unified Dashboard Layout
- **Sidebar Navigation:** Fixed sidebar for switching between **Academic Tree**, **GE Progress**, and **Schedule Builder**.
- **Global Actions:** A persistent "Upload Transcript" button in the sidebar or header to ingest student history (Excel/HTML).

### 2. Transcript Integration & Progress Tracking
- **Course History Ingestion:** Integrate `CourseInput` logic into the dashboard to process uploaded spreadsheets.
- **Progress Visualization (Tree):**
    - Automatically highlight nodes in the `CourseTree` based on the uploaded history.
    - Use distinct visual styles (e.g., green borders/glow) for **Completed** courses.
    - Dim or grayscale courses that are not yet available (prerequisites not met).
- **Progress Visualization (GE):** Ensure the `GeTracker` accurately reflects credits earned from the uploaded transcript.

### 3. Tree-Centric "Hero" View
- **Expanded Canvas:** The `CourseTree` takes up the full dashboard viewport.
- **Interactive Nodes:** Clicking a node opens the **Course Details Modal**.
- **Dynamic Filters:** Floating panel to filter by Department and completion status.

### 4. Central Course Details Modal
- High-fidelity modal replacing inline accordions.
- **Content:** Full description, units, and elective groups.
- **Status Badge:** Clearly show if the course is "Completed", "In Progress", or "Planned".

### 5. Modern Glassmorphism Aesthetic
- Semi-transparent panels with `backdrop-blur`.
- Animated transitions for switching views and opening modals.
- Polished typography and spacing following modern UX best practices.

## Acceptance Criteria
- [ ] Users can upload a transcript and see their completed courses highlighted on the tree.
- [ ] Sidebar navigation allows seamless switching between views.
- [ ] `GeTracker` correctly calculates and displays progress from uploaded data.
- [ ] All panels use the Glassmorphism visual style.
- [ ] Clicking a tree node opens a detailed modal with elective support.

## Out of Scope
- Direct manual editing of course history (upload-only for now).
- Multi-student profile persistence (local session-based only).
