import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ElectiveList from '../ElectiveList';
import React from 'react';

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
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: mockElectives }),
    } as Response);

    render(<ElectiveList poid="13772" />);

    await waitFor(() => {
      expect(screen.getByText('CS Electives')).toBeInTheDocument();
      expect(screen.getByText('Complete 9 units')).toBeInTheDocument();
    });
  });

  it('expands a group to show course choices', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: mockElectives }),
    } as Response);

    render(<ElectiveList poid="13772" />);

    await waitFor(() => {
      expect(screen.getByText('CS Electives')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('CS Electives'));

    expect(screen.getByText('CS 151')).toBeInTheDocument();
    expect(screen.getByText('CS 152')).toBeInTheDocument();
  });

  it('fetches course details when a course is clicked', async () => {
    vi.spyOn(global, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success', data: mockElectives }),
      } as Response)
      .mockResolvedValueOnce({
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

    render(<ElectiveList poid="13772" />);

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
