import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ElectiveList from '../ElectiveList';
import React from 'react';
import { PlannerProvider, usePlanner } from '../../context/PlannerContext';

const TestWrapper = ({ poid, electives }: { poid: string, electives: any[] }) => {
  const { loadMajorData } = usePlanner();

  React.useEffect(() => {
    // Mock the fetch just for this load
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.toString().includes('/api/electives/')) {
        return Promise.resolve({ ok: true, json: async () => ({ data: electives }) } as Response);
      }
      return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
    });

    loadMajorData(poid).finally(() => {
      global.fetch = originalFetch;
    });
  }, [poid, electives, loadMajorData]);

  return <ElectiveList poid={poid} />;
};

describe('ElectiveList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockElectives = [
    {
      heading: 'CS Electives',
      instructions: 'Complete 9 units',
      choices: ['CS 151', 'CS 152'],
    },
  ];

  it('fetches and displays elective groups', async () => {
    render(
      <PlannerProvider>
        <TestWrapper poid="13772" electives={mockElectives} />
      </PlannerProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('CS Electives')).toBeInTheDocument();
    });
    
    // Expand to see instructions
    fireEvent.click(screen.getByText('CS Electives'));
    expect(screen.getByText(/Complete 9 units/i)).toBeInTheDocument();
  });

  it('expands a group to show course choices', async () => {
    render(
      <PlannerProvider>
        <TestWrapper poid="13772" electives={mockElectives} />
      </PlannerProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('CS Electives')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('CS Electives'));

    expect(screen.getByText('CS 151')).toBeInTheDocument();
    expect(screen.getByText('CS 152')).toBeInTheDocument();
  });

  it('fetches course details when a course is clicked', async () => {
    vi.spyOn(global, 'fetch').mockImplementation((url) => {
      if (url.toString().includes('/api/course/')) {
         return Promise.resolve({
          ok: true,
          json: async () => ({
            status: 'success',
            data: {
              course_name: 'Object Oriented Design',
              description: 'Advanced Java programming',
              units: '3',
            },
          }),
        } as Response);
      }
      return Promise.reject(new Error('unhandled route'));
    });

    render(
      <PlannerProvider>
        <TestWrapper poid="13772" electives={mockElectives} />
      </PlannerProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('CS Electives')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('CS Electives'));
    
    await waitFor(() => {
      expect(screen.getByText('CS 151')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('CS 151'));

    await waitFor(() => {
      expect(screen.getByText('Object Oriented Design')).toBeInTheDocument();
      expect(screen.getByText('Advanced Java programming')).toBeInTheDocument();
    });
  });
});
