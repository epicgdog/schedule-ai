import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';

export interface GeAnalysisData {
  Name: string;
  Major: string;
  GE_Courses: Record<string, { Areas: string[]; Units: number; Courses: string[] }>;
  Major_Courses: Record<string, any>;
  POID?: string | number;
}

interface PlannerContextType {
  selectedPoid: string;
  setSelectedPoid: (poid: string) => void;
  courseHistory: GeAnalysisData | null;
  setCourseHistory: (history: GeAnalysisData | null) => void;
  plannedCourses: string[];
  setPlannedCourses: (courses: string[]) => void;
  
  // Cache and Loading State
  treeCache: Record<string, any>;
  electiveCache: Record<string, any>;
  loadingState: { tree: boolean; electives: boolean };
  loadMajorData: (poid: string) => Promise<void>;
}

const PlannerContext = createContext<PlannerContextType | undefined>(undefined);

export const PlannerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedPoid, setSelectedPoid] = useState<string>('13772');
  const [courseHistory, setCourseHistory] = useState<GeAnalysisData | null>(null);
  const [plannedCourses, setPlannedCourses] = useState<string[]>([]);

  // Cache State
  const [treeCache, setTreeCache] = useState<Record<string, any>>({});
  const [electiveCache, setElectiveCache] = useState<Record<string, any>>({});
  const [loadingState, setLoadingState] = useState({ tree: false, electives: false });

  const loadMajorData = useCallback(async (poid: string) => {
    if (!poid) return;

    const needsTree = !treeCache[poid];
    const needsElectives = !electiveCache[poid];

    if (!needsTree && !needsElectives) return;

    setLoadingState(prev => ({ 
      tree: prev.tree || needsTree, 
      electives: prev.electives || needsElectives 
    }));

    const promises = [];

    if (needsTree) {
      promises.push(
        fetch(`http://localhost:8000/api/course_tree/${encodeURIComponent(poid)}`)
          .then(res => {
            if (!res.ok) throw new Error('Failed to fetch tree');
            return res.json();
          })
          .then(data => {
            setTreeCache(prev => ({ ...prev, [poid]: data }));
          })
          .catch(err => console.error(err))
          .finally(() => setLoadingState(prev => ({ ...prev, tree: false })))
      );
    }

    if (needsElectives) {
      promises.push(
        fetch(`http://localhost:8000/api/electives/${encodeURIComponent(poid)}`)
          .then(res => {
            if (!res.ok) throw new Error('Failed to fetch electives');
            return res.json();
          })
          .then(data => {
            setElectiveCache(prev => ({ ...prev, [poid]: data.data || [] }));
          })
          .catch(err => console.error(err))
          .finally(() => setLoadingState(prev => ({ ...prev, electives: false })))
      );
    }

    await Promise.all(promises);
  }, [treeCache, electiveCache]);

  // Load data whenever the selected POID changes
  useEffect(() => {
    loadMajorData(selectedPoid);
  }, [selectedPoid, loadMajorData]);

  return (
    <PlannerContext.Provider
      value={{
        selectedPoid,
        setSelectedPoid,
        courseHistory,
        setCourseHistory,
        plannedCourses,
        setPlannedCourses,
        treeCache,
        electiveCache,
        loadingState,
        loadMajorData
      }}
    >
      {children}
    </PlannerContext.Provider>
  );
};

export const usePlanner = () => {
  const context = useContext(PlannerContext);
  if (context === undefined) {
    throw new Error('usePlanner must be used within a PlannerProvider');
  }
  return context;
};
