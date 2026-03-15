import React, { useEffect, useMemo, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { usePlanner } from '../context/PlannerContext';
import CourseDetailModal from './CourseDetailModal';
import Skeleton from './ui/Skeleton';

cytoscape.use(dagre);

type GraphNode = {
  data: {
    id: string;
    label: string;
    department?: string;
    is_root?: boolean;
    is_leaf?: boolean;
  };
};

type GraphEdge = {
  data: {
    source: string;
    target: string;
  };
};

type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  program_name?: string | null;
};

interface CourseTreeProps {
  poid: string;
}

const DEPT_COLORS: Record<string, string> = {
  CS: '#2f80ed',
  MATH: '#219653',
  ENGR: '#f2994a',
  CMPE: '#56ccf2',
  EE: '#f2c94c',
  PHYS: '#bb6bd9',
  CHEM: '#eb5757',
};

const CourseTree: React.FC<CourseTreeProps> = ({ poid }) => {
  const { courseHistory, treeCache, loadingState } = usePlanner();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const graph = treeCache[poid] as GraphResponse | undefined;
  const loading = loadingState.tree;
  const error = null; // Error handling can be moved to context later if needed
  const [hiddenDepts, setHiddenDepts] = useState<Set<string>>(new Set());

  // Modal state
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Helper to get all completed course codes
  const completedCourses = useMemo(() => {
    if (!courseHistory) return new Set<string>();
    
    const codes = new Set<string>();
    // Extract from Major_Courses
    Object.values(courseHistory.Major_Courses || {}).forEach((item: any) => {
      if (item.Courses) {
        item.Courses.forEach((c: string) => codes.add(c.trim()));
      }
    });
    // Extract from GE_Courses
    Object.values(courseHistory.GE_Courses || {}).forEach((item: any) => {
      if (item.Courses) {
        item.Courses.forEach((c: string) => codes.add(c.trim()));
      }
    });
    
    return codes;
  }, [courseHistory]);

  // Reset hidden departments when a new graph is loaded (none hidden by default)
  useEffect(() => {
    if (graph) {
      setHiddenDepts(new Set());
    }
  }, [graph]);

  const toggleDept = (dept: string) => {
    const newDepts = new Set(hiddenDepts);
    if (newDepts.has(dept)) {
      newDepts.delete(dept);
    } else {
      newDepts.add(dept);
    }
    setHiddenDepts(newDepts);
  };

  const allDepts = useMemo(() => {
    if (!graph) return [];
    const depts = new Set(graph.nodes.map(n => n.data.department || 'OTHER'));
    return Array.from(depts).sort();
  }, [graph]);

  const elements = useMemo(() => {
    if (!graph) return [];

    // Filter nodes: show if NOT in hiddenDepts
    const filteredNodes = graph.nodes.filter(node => 
      !hiddenDepts.has(node.data.department || 'OTHER')
    );
    const visibleNodeIds = new Set(filteredNodes.map(n => n.data.id));

    // Pre-calculate dependencies to determine "Available" status
    const nodePreReqs = new Map<string, string[]>();
    graph.edges.forEach(edge => {
      const target = edge.data.target;
      const source = edge.data.source;
      if (!nodePreReqs.has(target)) {
        nodePreReqs.set(target, []);
      }
      nodePreReqs.get(target)!.push(source);
    });

    const nodeEls = filteredNodes.map((node) => {
      const dept = node.data.department || 'OTHER';
      const color = DEPT_COLORS[dept] || '#6b7280';
      const isCompleted = completedCourses.has(node.data.label);
      
      let isAvailable = false;
      if (!isCompleted) {
        const prereqs = nodePreReqs.get(node.data.id) || [];
        // If all direct prerequisites are completed, it's available
        isAvailable = prereqs.every(prereqId => {
          const prereqNode = graph.nodes.find(n => n.data.id === prereqId);
          return prereqNode ? completedCourses.has(prereqNode.data.label) : true; 
        });
      }

      // If neither completed nor available (and has prereqs), it's locked
      const isLocked = !isCompleted && !isAvailable && (nodePreReqs.get(node.data.id) || []).length > 0;

      return {
        data: {
          ...node.data,
          color: isLocked ? '#475569' : color, // Dim color if locked
          borderColor: isCompleted ? '#4ade80' : isAvailable ? '#60a5fa' : (node.data.is_root ? '#f2c94c' : '#2d3748'),
          borderWidth: isCompleted || isAvailable ? 3 : 2,
          isCompleted,
          isAvailable,
          isLocked
        },
      };
    });

    // Filter edges (both source and target must be visible)
    const filteredEdges = graph.edges.map(edge => ({
      data: {
        ...edge.data,
        isCompleted: completedCourses.has(graph.nodes.find(n => n.data.id === edge.data.target)?.data.label || '')
      }
    })).filter(edge => 
      visibleNodeIds.has(edge.data.source) && visibleNodeIds.has(edge.data.target)
    );

    return [...nodeEls, ...filteredEdges];
  }, [graph, hiddenDepts, completedCourses]);

  useEffect(() => {
    if (!containerRef.current || !graph || loading || error) {
      return;
    }

    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 60,
        edgeSep: 20,
        rankSep: 110,
      } as unknown as cytoscape.LayoutOptions,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': 'data(color)',
            color: '#f7fafc',
            'font-size': '10px',
            'font-weight': 600,
            'text-wrap': 'wrap',
            'text-max-width': '90px',
            width: 58,
            height: 58,
            'border-width': 'data(borderWidth)',
            'border-color': 'data(borderColor)',
            'text-valign': 'center',
            'text-halign': 'center',
            'transition-property': 'background-color, border-color, opacity',
            'transition-duration': 200,
          },
        },
        {
          selector: 'node[?isCompleted]',
          style: {
            'shadow-blur': 15,
            'shadow-color': '#4ade80',
            'shadow-opacity': 0.5,
          }
        },
        {
          selector: 'node[?isAvailable]',
          style: {
            'shadow-blur': 15,
            'shadow-color': '#60a5fa',
            'shadow-opacity': 0.3,
          }
        },
        {
          selector: 'node[?isLocked]',
          style: {
            opacity: 0.5,
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.9,
            'transition-property': 'line-color, target-arrow-color, width, opacity',
            'transition-duration': 200,
          },
        },
        {
          selector: 'edge[?isCompleted]',
          style: {
            'line-color': '#4ade80',
            'target-arrow-color': '#4ade80',
            opacity: 0.6,
          }
        },
        {
          selector: 'node.highlighted',
          style: {
            width: 58,
            height: 58,
            'border-width': 4,
            'border-color': '#f2c94c',
            opacity: 1,
            'z-index': 999,
          }
        },
        {
          selector: 'edge.highlighted',
          style: {
            'line-color': '#f2c94c',
            'target-arrow-color': '#f2c94c',
            width: 4,
            opacity: 1,
            'z-index': 999,
          }
        },
        {
          selector: '.faded',
          style: {
            opacity: 0.1,
          }
        }
      ],
    });

    // Hover highlights
    cyRef.current.on('mouseover', 'node', (e) => {
      const node = e.target;
      const neighborhood = node.predecessors(); // All direct and indirect prereqs
      const cy = e.cy;
      
      cy.elements().addClass('faded');
      node.removeClass('faded');
      neighborhood.removeClass('faded').addClass('highlighted');
    });

    cyRef.current.on('mouseout', 'node', (e) => {
      const cy = e.cy;
      cy.elements().removeClass('faded highlighted');
    });

    // Handle clicks
    cyRef.current.on('tap', 'node', (e) => {
      const node = e.target;
      setSelectedCourse(node.data('label'));
      setIsModalOpen(true);
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [elements, graph, loading, error]);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="flex justify-between items-end">
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-8 w-16 rounded-full" />
            <Skeleton className="h-8 w-16 rounded-full" />
            <Skeleton className="h-8 w-16 rounded-full" />
          </div>
        </div>
        <Skeleton className="w-full h-[560px] rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-8 rounded-2xl border-red-500/20 text-center">
        <div className="text-red-400 font-bold mb-2">Failed to load tree</div>
        <div className="text-red-300/70 text-sm">{error}</div>
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return <div className="text-gray-400 py-20 text-center italic border border-dashed border-white/5 rounded-2xl">No required course graph found for POID {poid}.</div>;
  }

  return (
    <div className="flex flex-col h-[700px]">
      <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/5">
        <div>
          <h2 className="text-xl font-bold text-white leading-tight">{graph.program_name || `Program POID ${poid}`}</h2>
          <div className="flex items-center gap-4 mt-2">
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span>{graph.nodes.length} Courses</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              <span>{graph.edges.length} Prerequisites</span>
            </div>
            {completedCourses.size > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(74,222,128,0.5)]" />
                <span>{completedCourses.size} Completed</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-1">Filter Departments</span>
          <div className="flex flex-wrap gap-1.5">
            {allDepts.map(dept => {
              const isHidden = hiddenDepts.has(dept);
              const color = DEPT_COLORS[dept] || '#6b7280';
              return (
                <button
                  key={dept}
                  onClick={() => toggleDept(dept)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all border ${
                    !isHidden 
                      ? 'bg-white/5 text-white border-white/10 shadow-lg' 
                      : 'bg-transparent text-gray-600 border-white/5 opacity-40'
                  }`}
                  style={{ 
                    borderLeft: !isHidden ? `3px solid ${color}` : undefined,
                  }}
                >
                  {dept}
                </button>
              );
            })}
          </div>
        </div>
      </div>
      
      <div className="flex-1 relative bg-black/40 shadow-inner" ref={containerRef} />

      <CourseDetailModal 
        courseCode={selectedCourse}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default CourseTree;
