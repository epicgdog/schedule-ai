import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardLayout from '../DashboardLayout';
import React from 'react';

// Mock Sidebar to simplify layout tests
vi.mock('../Sidebar', () => ({
  default: () => <div data-testid="sidebar">Sidebar</div>,
}));

describe('DashboardLayout', () => {
  it('renders sidebar and children', () => {
    render(
      <DashboardLayout activeTab="tree" onTabChange={() => {}}>
        <div data-testid="child-content">Main Content</div>
      </DashboardLayout>
    );

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('provides a fixed-width container for content', () => {
    const { container } = render(
      <DashboardLayout activeTab="tree" onTabChange={() => {}}>
        <div>Content</div>
      </DashboardLayout>
    );
    
    // The main content area should have a left margin to account for the fixed sidebar (w-64 = 16rem)
    const mainContent = container.querySelector('main');
    expect(mainContent).toHaveClass('ml-64');
  });
});
