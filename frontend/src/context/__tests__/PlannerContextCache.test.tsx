import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PlannerProvider, usePlanner } from '../PlannerContext';
import React from 'react';

const TestComponent = () => {
  const { loadMajorData, treeCache, electiveCache, loadingState } = usePlanner();

  return (
    <div>
      <button onClick={() => loadMajorData('13772')}>Load Data</button>
      <div data-testid="loading-tree">{loadingState.tree.toString()}</div>
      <div data-testid="loading-elective">{loadingState.electives.toString()}</div>
      <div data-testid="tree-data">{treeCache['13772'] ? 'Tree Loaded' : 'No Tree'}</div>
      <div data-testid="elective-data">{electiveCache['13772'] ? 'Electives Loaded' : 'No Electives'}</div>
    </div>
  );
};

describe('PlannerContext Caching', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and caches data for a new poid', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation((url) => {
      if (url.includes('/api/course_tree/')) {
        return Promise.resolve({ ok: true, json: async () => ({ nodes: [], edges: [] }) } as Response);
      }
      if (url.includes('/api/electives/')) {
        return Promise.resolve({ ok: true, json: async () => ({ data: [] }) } as Response);
      }
      return Promise.reject(new Error('not mocked'));
    });

    render(
      <PlannerProvider>
        <TestComponent />
      </PlannerProvider>
    );

    fireEvent.click(screen.getByText('Load Data'));

    // Loading states should be true initially
    expect(screen.getByTestId('loading-tree')).toHaveTextContent('true');
    expect(screen.getByTestId('loading-elective')).toHaveTextContent('true');

    // Wait for the fetches to resolve
    await waitFor(() => {
      expect(screen.getByTestId('tree-data')).toHaveTextContent('Tree Loaded');
      expect(screen.getByTestId('elective-data')).toHaveTextContent('Electives Loaded');
      expect(screen.getByTestId('loading-tree')).toHaveTextContent('false');
      expect(screen.getByTestId('loading-elective')).toHaveTextContent('false');
    });

    fetchSpy.mockClear();

    // Call loadData again, it should use the cache and NOT call fetch
    fireEvent.click(screen.getByText('Load Data'));

    // Wait a tick to ensure no further async actions occur
    await new Promise(resolve => setTimeout(resolve, 0));

    // Fetch should NOT have been called because data is cached
    expect(fetchSpy).toHaveBeenCalledTimes(0);
  });

  it('hydrates and persists to localStorage', async () => {
    const mockTreeCache = { '13772': { nodes: [{ data: { id: 'test' } }], edges: [] } };
    localStorage.setItem('planner_treeCache', JSON.stringify(mockTreeCache));

    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation((url) => {
      if (url.includes('/api/course_tree/')) {
        return Promise.resolve({ ok: true, json: async () => ({ nodes: [{ data: { id: 'new-test' } }], edges: [] }) } as Response);
      }
      if (url.includes('/api/electives/')) {
        return Promise.resolve({ ok: true, json: async () => ({ data: [] }) } as Response);
      }
      return Promise.reject(new Error('not mocked'));
    });

    const TestPersistenceComponent = () => {
      const { treeCache, loadMajorData } = usePlanner();
      return (
        <div>
          <div data-testid="hydrated-data">{treeCache['13772'] ? 'Hydrated' : 'Empty'}</div>
          <button onClick={() => loadMajorData('999')}>
            Update Cache
          </button>
        </div>
      );
    };

    render(
      <PlannerProvider>
        <TestPersistenceComponent />
      </PlannerProvider>
    );

    // Should hydrate on mount
    expect(screen.getByTestId('hydrated-data')).toHaveTextContent('Hydrated');

    // Update state to trigger persist by loading a new major
    fireEvent.click(screen.getByText('Update Cache'));

    // Wait for the effect to run and fetch to complete
    await waitFor(() => {
      const savedCache = JSON.parse(localStorage.getItem('planner_treeCache') || '{}');
      expect(savedCache['999']).toBeDefined();
    });
  });
});
