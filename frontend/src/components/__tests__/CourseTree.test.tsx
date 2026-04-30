import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CourseTree from '../CourseTree';
import React from 'react';
import { PlannerProvider } from '../../context/PlannerContext';

// Mock cytoscape since it needs a DOM element and is complex to test in jsdom
vi.mock('cytoscape', () => {
  const mockCy = {
    on: vi.fn(),
    destroy: vi.fn(),
    elements: vi.fn(() => ({
      addClass: vi.fn(),
      removeClass: vi.fn(),
    })),
  };
  const mockFunc = vi.fn(() => mockCy);
  (mockFunc as any).use = vi.fn();
  return {
    default: mockFunc,
  };
});

describe('CourseTree', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockGraph = {
    program_name: 'Computer Science, BS',
    nodes: [
      { data: { id: 'CS46A', label: 'CS 46A', department: 'CS' } },
      { data: { id: 'MATH30', label: 'MATH 30', department: 'MATH' } },
    ],
    edges: [
      { data: { source: 'MATH30', target: 'CS46A' } },
    ],
  };

  it('fetches and displays the course tree info', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraph,
    } as Response);

    render(
      <PlannerProvider>
        <CourseTree poid="13772" />
      </PlannerProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Computer Science, BS/i)).toBeInTheDocument();
      expect(screen.getByText('CS')).toBeInTheDocument();
      expect(screen.getByText('MATH')).toBeInTheDocument();
    });
  });

  it('toggles department filters', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraph,
    } as Response);

    render(
      <PlannerProvider>
        <CourseTree poid="13772" />
      </PlannerProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('CS')).toBeInTheDocument();
    });

    const csButton = screen.getByText('CS');
    // Initially active
    expect(csButton).not.toHaveClass('bg-transparent');

    fireEvent.click(csButton);
    // Should now be hidden/deactivated
    expect(csButton).toHaveClass('bg-transparent', 'text-gray-600');
  });
});
