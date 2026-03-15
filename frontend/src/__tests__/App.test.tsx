import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import App from '../App';
import React from 'react';
import { PlannerProvider } from '../context/PlannerContext';

// Mock child components to simplify App tests
vi.mock('../components/MajorDropdown', () => ({
  default: ({ selectedPoid, onSelect }: any) => (
    <select 
      data-testid="major-select" 
      value={selectedPoid} 
      onChange={(e) => onSelect(e.target.value)}
    >
      <option value="13772">CS BS</option>
      <option value="12345">SE BS</option>
    </select>
  ),
}));

vi.mock('../components/CourseTree', () => ({
  default: ({ poid }: any) => <div data-testid="course-tree">Tree for {poid}</div>,
}));

vi.mock('../components/ElectiveList', () => ({
  default: ({ poid }: any) => <div data-testid="elective-list">Electives for {poid}</div>,
}));

vi.mock('../components/DashboardLayout', () => ({
  default: ({ children, activeTab, onTabChange }: any) => (
    <div data-testid="layout">
      <div data-testid="tab-indicator">{activeTab}</div>
      <button onClick={() => onTabChange('ge')}>Switch to GE</button>
      {children}
    </div>
  ),
}));

describe('App', () => {
  it('renders correctly and manages selected poid', async () => {
    render(
      <PlannerProvider>
        <App />
      </PlannerProvider>
    );

    expect(screen.getByText(/Academic Planner/i)).toBeInTheDocument();
    expect(screen.getByTestId('course-tree')).toHaveTextContent('Tree for 13772');
    expect(screen.getByTestId('elective-list')).toHaveTextContent('Electives for 13772');

    fireEvent.change(screen.getByTestId('major-select'), { target: { value: '12345' } });

    expect(screen.getByTestId('course-tree')).toHaveTextContent('Tree for 12345');
    expect(screen.getByTestId('elective-list')).toHaveTextContent('Electives for 12345');
  });

  it('manages active tab state', () => {
    render(
      <PlannerProvider>
        <App />
      </PlannerProvider>
    );
    
    expect(screen.getByTestId('tab-indicator')).toHaveTextContent('tree');
    
    // Check that GE Progress is in the document but visually hidden
    const geSection = screen.getByText(/GE Progress Tracker/i).closest('section');
    expect(geSection).toHaveClass('hidden');

    fireEvent.click(screen.getByText(/Switch to GE/i));
    
    expect(screen.getByTestId('tab-indicator')).toHaveTextContent('ge');
    
    // Now GE should NOT be hidden
    expect(geSection).not.toHaveClass('hidden');
    
    // And Tree should be hidden
    const treeSection = screen.getByTestId('course-tree').closest('div.space-y-8')?.parentElement;
    expect(treeSection).toHaveClass('hidden');
  });
});
