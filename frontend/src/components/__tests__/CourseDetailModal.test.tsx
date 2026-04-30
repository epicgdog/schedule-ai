import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CourseDetailModal from '../CourseDetailModal';
import React from 'react';

describe('CourseDetailModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays course details when opened', async () => {
    const mockDetails = {
      course_name: 'Introduction to Programming',
      description: 'Learn to code with Python.',
      units: '3'
    };

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: mockDetails }),
    } as Response);

    render(
      <CourseDetailModal 
        courseCode="CS 46A" 
        isOpen={true} 
        onClose={() => {}} 
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Introduction to Programming/i)).toBeInTheDocument();
      expect(screen.getByText(/Learn to code with Python/i)).toBeInTheDocument();
      expect(screen.getByText(/3 Units/i)).toBeInTheDocument();
    });
  });
});
