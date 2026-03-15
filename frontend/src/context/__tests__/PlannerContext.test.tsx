import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PlannerProvider, usePlanner } from '../PlannerContext';
import React from 'react';

const TestComponent = () => {
  const { selectedPoid, setSelectedPoid, courseHistory, setCourseHistory } = usePlanner();
  return (
    <div>
      <div data-testid="poid">{selectedPoid}</div>
      <button onClick={() => setSelectedPoid('12345')}>Change POID</button>
      <div data-testid="history-count">{Object.keys(courseHistory?.GE_Courses || {}).length}</div>
      <button onClick={() => setCourseHistory({ Name: 'Test', Major: 'CS', GE_Courses: { 'A': { Areas: ['A1'], Units: 3, Courses: ['CS 1'] } }, Major_Courses: {} })}>
        Set History
      </button>
    </div>
  );
};

describe('PlannerContext', () => {
  it('provides default values and updates state', () => {
    render(
      <PlannerProvider>
        <TestComponent />
      </PlannerProvider>
    );

    expect(screen.getByTestId('poid')).toHaveTextContent('13772');
    expect(screen.getByTestId('history-count')).toHaveTextContent('0');

    fireEvent.click(screen.getByText('Change POID'));
    expect(screen.getByTestId('poid')).toHaveTextContent('12345');

    fireEvent.click(screen.getByText('Set History'));
    expect(screen.getByTestId('history-count')).toHaveTextContent('1');
  });
});
