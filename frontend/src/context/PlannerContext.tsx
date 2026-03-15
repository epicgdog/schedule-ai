import React, { createContext, useContext, useState, ReactNode } from 'react';

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
}

const PlannerContext = createContext<PlannerContextType | undefined>(undefined);

export const PlannerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedPoid, setSelectedPoid] = useState<string>('13772');
  const [courseHistory, setCourseHistory] = useState<GeAnalysisData | null>(null);
  const [plannedCourses, setPlannedCourses] = useState<string[]>([]);

  return (
    <PlannerContext.Provider
      value={{
        selectedPoid,
        setSelectedPoid,
        courseHistory,
        setCourseHistory,
        plannedCourses,
        setPlannedCourses,
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
