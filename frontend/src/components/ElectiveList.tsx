import React, { useState, useMemo } from 'react';
import { ChevronDown, BookOpen, Info, Loader2, CheckCircle2 } from 'lucide-react';
import Skeleton from './ui/Skeleton';
import { usePlanner } from '../context/PlannerContext';

interface ElectiveGroup {
  heading: string;
  instructions: string;
  choices: string[];
}

interface CourseDetails {
  course_name: string;
  description: string;
  units: string;
}

interface ElectiveListProps {
  poid: string;
}

const ElectiveCourseItem: React.FC<{ code: string; isCompleted: boolean }> = ({ code, isCompleted }) => {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<CourseDetails | null>(null);
  const [loading, setLoading] = useState(false);

  const toggleExpand = async () => {
    if (!expanded && !details) {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/course/${encodeURIComponent(code)}`);
        if (response.ok) {
          const data = await response.json();
          setDetails(data.data);
        }
      } catch (err) {
        console.error("Failed to fetch course details:", err);
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  return (
    <div className="w-full">
      <button
        onClick={toggleExpand}
        className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex justify-between items-center group ${
          isCompleted
            ? 'bg-green-500/10 border-green-500/30 text-green-400 shadow-[0_0_15px_rgba(74,222,128,0.1)]'
            : expanded 
              ? 'bg-blue-600/10 border-blue-500/30 text-blue-400 shadow-[0_0_15px_rgba(37,99,235,0.1)]' 
              : 'bg-white/5 border-white/5 text-gray-400 hover:border-white/10 hover:text-white'
        }`}
      >
        <div className="flex items-center gap-2">
          {isCompleted ? (
             <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
          ) : (
             <BookOpen className={`w-3.5 h-3.5 transition-colors ${expanded ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-300'}`} />
          )}
          <span className="text-xs font-bold tracking-wide uppercase">{code}</span>
        </div>
        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-300 ${expanded ? 'rotate-180' : 'opacity-40'}`} />
      </button>
      
      {expanded && (
        <div className={`mt-2 p-4 bg-black/40 border rounded-2xl animate-in fade-in slide-in-from-top-2 duration-300 ${isCompleted ? 'border-green-500/20' : 'border-white/5'}`}>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/4" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : details ? (
            <div className="space-y-3">
              <div className={`font-bold text-sm leading-tight ${isCompleted ? 'text-green-300' : 'text-white'}`}>{details.course_name}</div>
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                {details.units} Units
              </div>
              <div className="text-gray-400 leading-relaxed text-xs">
                {details.description || "No description available."}
              </div>
            </div>
          ) : (
            <div className="text-red-400 text-xs flex items-center gap-2">
              <Info className="w-3.5 h-3.5" />
              <span>Details not found.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const ElectiveList: React.FC<ElectiveListProps> = ({ poid }) => {
  const { electiveCache, loadingState, courseHistory } = usePlanner();
  const electives: ElectiveGroup[] = electiveCache[poid] || [];
  const loading = loadingState.electives;
  const error = null;
  const [expandedGroup, setExpandedGroup] = useState<number | null>(null);

  const completedCourses = useMemo(() => {
    if (!courseHistory) return new Set<string>();
    
    const codes = new Set<string>();
    Object.values(courseHistory.Major_Courses || {}).forEach((item: any) => {
      if (item.Courses) {
        item.Courses.forEach((c: string) => codes.add(c.trim()));
      }
    });
    Object.values(courseHistory.GE_Courses || {}).forEach((item: any) => {
      if (item.Courses) {
        item.Courses.forEach((c: string) => codes.add(c.trim()));
      }
    });
    
    return codes;
  }, [courseHistory]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="space-y-3">
          <Skeleton className="h-16 w-full rounded-2xl" />
          <Skeleton className="h-16 w-full rounded-2xl" />
          <Skeleton className="h-16 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center border border-red-500/20 bg-red-500/5 rounded-2xl">
        <div className="text-red-400 font-bold text-sm mb-1">Failed to load electives</div>
        <div className="text-red-300/60 text-xs">{error}</div>
      </div>
    );
  }

  if (electives.length === 0) return null;

  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-3">
          <div className="w-1.5 h-6 bg-blue-500 rounded-full" />
          Program Electives
        </h2>
        <p className="text-gray-500 text-sm mt-1 ml-4.5 font-medium">Explore elective options required for your major.</p>
      </header>
      
      <div className="space-y-4">
        {electives.map((group, idx) => {
          const isExpanded = expandedGroup === idx;
          return (
            <div key={idx} className={`glass-panel border transition-all duration-500 rounded-2xl overflow-hidden ${
              isExpanded ? 'border-white/10 shadow-2xl' : 'border-white/5 hover:border-white/10'
            }`}>
              <button
                onClick={() => setExpandedGroup(isExpanded ? null : idx)}
                className={`w-full flex items-center justify-between p-5 text-left transition-colors ${
                  isExpanded ? 'bg-white/5 border-b border-white/5' : 'hover:bg-white/5'
                }`}
              >
                <div className="space-y-1">
                  <h3 className={`text-base font-bold transition-colors ${isExpanded ? 'text-blue-400' : 'text-white'}`}>
                    {group.heading}
                  </h3>
                  <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-none">
                    {group.choices.length} Available Choices
                  </p>
                </div>
                <div className={`p-2 rounded-xl transition-all duration-300 ${isExpanded ? 'bg-blue-500/10 text-blue-400 rotate-180' : 'bg-white/5 text-gray-500'}`}>
                  <ChevronDown className="w-4 h-4" />
                </div>
              </button>
              
              {isExpanded && (
                <div className="p-6 bg-black/20 animate-in fade-in slide-in-from-top-4 duration-500">
                  <div className="flex items-start gap-3 mb-6 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                    <Info className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-gray-300 leading-relaxed italic">
                      <span className="font-bold text-blue-400 not-italic uppercase text-[10px] tracking-widest block mb-1">Requirement Instructions</span>
                      {group.instructions}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {group.choices.map((choice, cIdx) => (
                      <ElectiveCourseItem key={cIdx} code={choice} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ElectiveList;
