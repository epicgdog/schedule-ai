import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TranscriptUploader from '../TranscriptUploader';
import React from 'react';
import { PlannerProvider } from '../../context/PlannerContext';

describe('TranscriptUploader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles file upload and updates context', async () => {
    const mockData = {
      Name: 'John Doe',
      Major: 'Computer Science',
      GE_Courses: {},
      Major_Courses: {},
      POID: '13772'
    };

    vi.spyOn(global, 'fetch').mockImplementation((url) => {
      if (url.includes('/api/generate_classes')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'success', text: JSON.stringify(mockData) }),
        } as Response);
      }
      return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
    });

    render(
      <PlannerProvider>
        <TranscriptUploader />
      </PlannerProvider>
    );

    const button = screen.getByText(/Upload Record/i);
    expect(button).toBeInTheDocument();

    // Mock file selection
    const file = new File(['test'], 'transcript.xls', { type: 'application/vnd.ms-excel' });
    const input = screen.getByTestId('file-input');
    
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Processing/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/Upload Record/i)).toBeInTheDocument();
    });
  });
});
