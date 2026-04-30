import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import GeTracker from '../GeTracker';
import React from 'react';
import { PlannerProvider } from '../../context/PlannerContext';

describe('GeTracker', () => {
  const mockGeCourses = {
    "A": { "Areas": ["A1", "A2"], "Units": 6, "Courses": ["ENGL 1A", "COMM 20"] },
    "B": { "Areas": ["B4"], "Units": 3, "Courses": ["MATH 30"] }
  };

  it('renders progress correctly', () => {
    render(
      <PlannerProvider>
        <GeTracker geCourses={mockGeCourses} />
      </PlannerProvider>
    );
    
    expect(screen.getByText(/GE Progress Tracker/i)).toBeInTheDocument();
    expect(screen.getByText('Area A')).toBeInTheDocument();
    expect(screen.getByText('Basic Skills')).toBeInTheDocument();
    
    // Check for units
    expect(screen.getByText(/6 \/ 9/i)).toBeInTheDocument();
  });

  it('shows sub-area completion', () => {
    render(
      <PlannerProvider>
        <GeTracker geCourses={mockGeCourses} />
      </PlannerProvider>
    );
    
    // Check for area badges
    expect(screen.getByText(/A1/i)).toBeInTheDocument();
    expect(screen.getByText(/A2/i)).toBeInTheDocument();
    
    // Check that A3 appears
    expect(screen.getAllByText(/A3/i).length).toBeGreaterThanOrEqual(1);
  });
});
