import React, { useState } from 'react';
import { CheckCircle2, Circle, Search, Loader2, ChevronRight } from 'lucide-react';
import { usePlanner } from '../context/PlannerContext';

// Configuration as per user request
const GE_UNITS_REQUIRED: Record<string, { Areas: string[], Units: number, Label: string }> = {
    "A": { "Areas": ["A1", "A2", "A3"], "Units": 9, "Label": "Basic Skills" },
    "B": { "Areas": ["B1", "B2", "B3", "B4"], "Units": 9, "Label": "Science & Math" },
    "C": { "Areas": ["C1", "C2"], "Units": 9, "Label": "Arts & Humanities" },
    "D": { "Areas": ["D"], "Units": 6, "Label": "Social Sciences" },
    "F": { "Areas": ["F"], "Units": 3, "Label": "Ethnic Studies" },
    "US": { "Areas": ["US1", "US2", "US3"], "Units": 6, "Label": "US History, Constitution, & California Govt" },
    "UPPER": { "Areas": ["R", "S", "V"], "Units": 9, "Label": "SJSU Studies (Upper Division)" },
    "PE": { "Areas": ["PE"], "Units": 2, "Label": "Physical Education" }
};

interface GeCourseProgress {
    Areas: string[];
    Units: number;
    Courses?: string[];
}

interface GeTrackerProps {
    geCourses?: Record<string, GeCourseProgress>;
}

const GeTracker: React.FC<GeTrackerProps> = ({ geCourses: propsGeCourses }) => {
    const { courseHistory } = usePlanner();
    const geCourses = propsGeCourses || courseHistory?.GE_Courses || {};
    
    const [openClasses, setOpenClasses] = useState<Record<string, any[]>>({});
    const [loadingArea, setLoadingArea] = useState<string | null>(null);
    const [expandedArea, setExpandedArea] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchOpenClasses = async (area: string) => {
        if (openClasses[area]) {
            setExpandedArea(expandedArea === area ? null : area);
            return;
        }

        setLoadingArea(area);
        setError(null);
        try {
            const response = await fetch(`/api/open_ge_classes/${area}`);
            if (!response.ok) throw new Error('Failed to fetch classes');

            const data = await response.json();
            setOpenClasses(prev => ({
                ...prev,
                [area]: data.classes
            }));
            setExpandedArea(area);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load classes');
        } finally {
            setLoadingArea(null);
        }
    };

    const categories = Object.keys(GE_UNITS_REQUIRED);

    return (
        <div className="w-full space-y-8">
            <header>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">GE Progress Tracker</h2>
                <p className="text-gray-400 mt-1">Track your SJSU general education requirements and find open sections.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {categories.map((catKey) => {
                    const requirements = GE_UNITS_REQUIRED[catKey];
                    const progress = geCourses[catKey] || { Areas: [], Units: 0, Courses: [] };

                    const neededAreas = requirements.Areas.filter(a => !progress.Areas.includes(a));
                    const isCompleted = progress.Units >= requirements.Units && neededAreas.length === 0;
                    const isPartial = progress.Units > 0 || progress.Areas.length > 0;

                    let status: 'completed' | 'partial' | 'missing' = 'missing';
                    if (isCompleted) status = 'completed';
                    else if (isPartial) status = 'partial';

                    const isOpen = expandedArea === catKey;

                    return (
                        <div
                            key={catKey}
                            className={`glass-panel p-6 rounded-2xl border transition-all duration-300 flex flex-col group ${
                                status === 'completed'
                                    ? 'border-green-500/20 bg-green-500/5'
                                    : status === 'partial'
                                        ? 'border-blue-500/20 bg-blue-500/5'
                                        : 'border-white/5 hover:border-white/10'
                            }`}
                        >
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-xl font-bold text-white tracking-tight">Area {catKey}</h3>
                                        {status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-400" />}
                                    </div>
                                    <p className="text-xs text-gray-500 font-medium mt-1 leading-relaxed">{requirements.Label}</p>
                                </div>
                                <div className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg ${
                                    status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                    status === 'partial' ? 'bg-blue-500/20 text-blue-400' :
                                    'bg-white/5 text-gray-500'
                                }`}>
                                    {status === 'completed' ? 'Done' : status === 'partial' ? 'In Progress' : 'Missing'}
                                </div>
                            </div>

                            <div className="space-y-4 mb-6">
                                <div>
                                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-2">
                                        <span>Units Earned</span>
                                        <span className={status === 'completed' ? 'text-green-400' : 'text-gray-300'}>
                                            {Math.min(requirements.Units, progress.Units)} / {requirements.Units}
                                        </span>
                                    </div>
                                    <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden border border-white/5">
                                        <div
                                            className={`h-full rounded-full transition-all duration-1000 ease-out ${
                                                status === 'completed' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]' :
                                                status === 'partial' ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.4)]' :
                                                'bg-gray-800'
                                            }`}
                                            style={{ width: `${Math.min(100, (progress.Units / requirements.Units) * 100)}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="flex flex-wrap gap-1.5">
                                    {requirements.Areas.map(area => {
                                        const isDone = progress.Areas.includes(area);
                                        return (
                                            <span
                                                key={area}
                                                className={`px-2 py-1 text-[10px] font-bold rounded-lg border transition-colors ${
                                                    isDone
                                                        ? 'bg-green-500/10 border-green-500/20 text-green-400'
                                                        : 'bg-white/5 border-white/5 text-gray-500'
                                                }`}
                                            >
                                                {area}
                                            </span>
                                        );
                                    })}
                                </div>
                            </div>

                            {progress.Courses && progress.Courses.length > 0 && (
                                <div className="mb-6 bg-black/20 rounded-xl p-3 border border-white/5">
                                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 px-1">Applied Courses</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {progress.Courses.map((c, i) => (
                                            <span key={i} className="text-xs text-gray-300 bg-white/5 px-2 py-1 rounded-md border border-white/5">{c}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="mt-auto pt-4 border-t border-white/5">
                                {neededAreas.length > 0 ? (
                                    <button
                                        onClick={() => fetchOpenClasses(neededAreas[0])}
                                        disabled={loadingArea === neededAreas[0]}
                                        className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 border ${
                                            isOpen 
                                                ? 'bg-white/10 border-white/10 text-white' 
                                                : 'bg-blue-600/10 border-blue-500/20 text-blue-400 hover:bg-blue-600/20'
                                        }`}
                                    >
                                        {loadingArea === neededAreas[0] ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <>
                                                <Search className="w-3.5 h-3.5" />
                                                <span>{isOpen ? 'Close Open Sections' : `Find ${neededAreas[0]} Sections`}</span>
                                            </>
                                        )}
                                    </button>
                                ) : (
                                    <div className="py-2.5 text-center text-[10px] font-bold uppercase tracking-widest text-green-500/50">
                                        Requirement Satisfied
                                    </div>
                                )}
                            </div>

                            {isOpen && (
                                <div className="mt-4 space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                                    {openClasses[neededAreas[0]]?.length === 0 ? (
                                        <p className="text-xs text-gray-500 italic py-4 text-center">No open sections found for this term.</p>
                                    ) : (
                                        openClasses[neededAreas[0]]?.map((cls: any, idx: number) => (
                                            <div key={idx} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
                                                <div className="flex justify-between items-start mb-1">
                                                    <span className="text-xs font-bold text-blue-400">{cls.course_name}</span>
                                                    <span className="text-[10px] font-bold text-green-500/80 bg-green-500/10 px-1.5 py-0.5 rounded uppercase">{cls.open_seats} Seats</span>
                                                </div>
                                                <div className="flex justify-between items-end">
                                                    <div className="text-[10px] text-gray-400">
                                                        <p>{cls.days} • {cls.start_time}-{cls.end_time}</p>
                                                        <p className="mt-0.5 text-gray-500 italic">{cls.instructor}</p>
                                                    </div>
                                                    <button className="p-1.5 rounded-lg bg-white/5 hover:bg-blue-500/20 text-gray-400 hover:text-blue-400 transition-colors">
                                                        <ChevronRight className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-xs font-medium text-center">
                    {error}
                </div>
            )}
        </div>
    );
};

export default GeTracker;
