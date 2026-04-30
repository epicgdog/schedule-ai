import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GlassButton from '../GlassButton';
import React from 'react';

describe('GlassButton', () => {
  it('renders with label', () => {
    render(<GlassButton>Click Me</GlassButton>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<GlassButton onClick={handleClick}>Click Me</GlassButton>);
    fireEvent.click(screen.getByText(/click me/i));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('can be disabled', () => {
    render(<GlassButton disabled>Disabled</GlassButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
