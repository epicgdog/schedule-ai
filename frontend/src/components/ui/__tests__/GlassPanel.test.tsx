import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import GlassPanel from '../GlassPanel';
import React from 'react';

describe('GlassPanel', () => {
  it('renders children correctly', () => {
    render(<GlassPanel>Test Content</GlassPanel>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies default glass classes', () => {
    const { container } = render(<GlassPanel>Content</GlassPanel>);
    expect(container.firstChild).toHaveClass('glass-panel');
  });

  it('applies custom className', () => {
    const { container } = render(<GlassPanel className="custom-class">Content</GlassPanel>);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
