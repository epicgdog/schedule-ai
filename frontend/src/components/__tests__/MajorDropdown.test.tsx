import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MajorDropdown from '../MajorDropdown';
import React from 'react';

describe('MajorDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays programs', async () => {
    const mockPrograms = [
      { poid: '1', program_name: 'Computer Science' },
      { poid: '2', program_name: 'Software Engineering' },
    ];

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: mockPrograms }),
    } as Response);

    const onSelect = vi.fn();
    render(<MajorDropdown selectedPoid="" onSelect={onSelect} />);

    expect(screen.getByText(/Loading majors.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Computer Science')).toBeInTheDocument();
      expect(screen.getByText('Software Engineering')).toBeInTheDocument();
    });
  });

  it('calls onSelect when a major is chosen', async () => {
    const mockPrograms = [
      { poid: '1', program_name: 'Computer Science' },
    ];

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: mockPrograms }),
    } as Response);

    const onSelect = vi.fn();
    render(<MajorDropdown selectedPoid="" onSelect={onSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Computer Science')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByRole('combobox'), { target: { value: '1' } });
    expect(onSelect).toHaveBeenCalledWith('1');
  });

  it('displays error message on fetch failure', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network error'));

    render(<MajorDropdown selectedPoid="" onSelect={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Error: Network error/i)).toBeInTheDocument();
    });
  });
});
