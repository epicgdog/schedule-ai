import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import Sidebar from '../Sidebar';
import React from 'react';
import { PlannerProvider } from '../../context/PlannerContext';

describe('Sidebar', () => {
  it('renders all navigation items', () => {
    render(
      <PlannerProvider>
        <Sidebar activeTab="tree" onTabChange={() => {}} />
      </PlannerProvider>
    );
    expect(screen.getByText(/Academic Tree/i)).toBeInTheDocument();
    expect(screen.getByText(/GE Progress/i)).toBeInTheDocument();
    expect(screen.getByText(/^Schedule$/i)).toBeInTheDocument();
    expect(screen.getByText(/Course Search/i)).toBeInTheDocument();
    expect(screen.getByText(/Instructor Ratings/i)).toBeInTheDocument();
  });

  it('renders section headers', () => {
    render(
      <PlannerProvider>
        <Sidebar activeTab="tree" onTabChange={() => {}} />
      </PlannerProvider>
    );
    expect(screen.getByText(/Transcript Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Planner/i)).toBeInTheDocument();
  });

  it('calls onTabChange when an item is clicked', () => {
    const onTabChange = vi.fn();
    render(
      <PlannerProvider>
        <Sidebar activeTab="tree" onTabChange={onTabChange} />
      </PlannerProvider>
    );
    
    fireEvent.click(screen.getByText(/GE Progress/i));
    expect(onTabChange).toHaveBeenCalledWith('ge');
  });

  it('highlights the active tab', () => {
    render(
      <PlannerProvider>
        <Sidebar activeTab="ge" onTabChange={() => {}} />
      </PlannerProvider>
    );
    const geButton = screen.getByText(/GE Progress/i).closest('button');
    // Active class is bg-blue-600/20
    expect(geButton).toHaveClass('bg-blue-600/20');
  });
});
