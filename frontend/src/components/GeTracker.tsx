import React, { useState } from 'react';

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
    geCourses: Record<string, GeCourseProgress>;
}

const GeTracker: React.FC<GeTrackerProps> = ({ geCourses }) => {
    const [openClasses, setOpenClasses] = useState<Record<string, any[]>>({}); // Just use any[] for now or define type
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
            const response = await fetch(`http://localhost:8000/api/open_ge_classes/${area}`);
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
        <div className="w-full mt-8 p-6 bg-gray-900 rounded-lg border border-gray-700">
            <h2 className="text-2xl font-bold mb-6 text-white border-b border-gray-700 pb-2">GE Progress Tracker</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categories.map((catKey) => {
                    const requirements = GE_UNITS_REQUIRED[catKey];
                    const progress = geCourses[catKey] || { Areas: [], Units: 0, Courses: [] };

                    const neededAreas = requirements.Areas.filter(a => !progress.Areas.includes(a));
                    const isCompleted = progress.Units >= requirements.Units && neededAreas.length === 0;
                    const isPartial = progress.Units > 0 || progress.Areas.length > 0;

                    // Determine Status
                    let status: 'completed' | 'partial' | 'missing' = 'missing';
                    if (isCompleted) status = 'completed';
                    else if (isPartial) status = 'partial';

                    const isOpen = expandedArea === catKey;

                    return (
                        <div
                            key={catKey}
                            className={`p-5 rounded-lg border transition-all flex flex-col ${status === 'completed'
                                ? 'bg-green-900/20 border-green-700/50'
                                : status === 'partial'
                                    ? 'bg-yellow-900/10 border-yellow-700/40'
                                    : 'bg-gray-800 border-gray-700 hover:border-blue-500/50'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-xl font-bold text-gray-100">Area {catKey}</h3>
                                        {status === 'completed' && (
                                            <span className="text-green-400 text-lg">✓</span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-400 font-medium">{requirements.Label}</p>
                                </div>
                                <div className={`px-2 py-1 text-xs font-semibold rounded-full ${status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                    status === 'partial' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                                    }`}>
                                    {status === 'completed' ? 'Done' : status === 'partial' ? 'In Progress' : 'Missing'}
                                </div>
                            </div>

                            {/* Units Progress Bar */}
                            <div className="mb-4">
                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                    <span>{
                                        progress.Units > requirements.Units ?
                                            requirements.Units
                                            : progress.Units
                                        } / {requirements.Units} Units</span>
                                    <span>{
                                        ((progress.Units / requirements.Units) * 100 > 100) ?
                                            100
                                             : Math.round((progress.Units / requirements.Units) * 100)

                                    }%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all duration-500 ${status === 'completed' ? 'bg-green-500' :
                                            status === 'partial' ? 'bg-yellow-500' : 'bg-gray-600'
                                            }`}
                                        style={{ width: `${Math.min(100, (progress.Units / requirements.Units) * 100)}%` }}
                                    />
                                </div>
                            </div>

                            {/* Sub-Areas Status */}
                            <div className="flex-1">
                                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Requirements</h4>
                                <div className="flex flex-wrap gap-2 mb-3">
                                    {requirements.Areas.map(area => {
                                        const isDone = progress.Areas.includes(area);
                                        return (
                                            <span
                                                key={area}
                                                className={`px-2 py-1 text-xs rounded border ${isDone
                                                    ? 'bg-green-900/30 border-green-600/50 text-green-300'
                                                    : 'bg-gray-700 border-gray-600 text-gray-400'
                                                    }`}
                                            >
                                                {area} {isDone && '✓'}
                                            </span>
                                        );
                                    })}
                                </div>

                                {/* Courses Taken */}
                                {progress.Courses && progress.Courses.length > 0 && (
                                    <div className="mb-3">
                                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Courses Applied</h4>
                                        <ul className="text-sm text-gray-300 space-y-1">
                                            {progress.Courses.map((c, i) => (
                                                <li key={i} className="truncate">• {c}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            {/* Action Button: Find Classes for Missing Areas */}
                            {neededAreas.length > 0 && (
                                <div className="mt-4 pt-3 border-t border-gray-700/50">
                                    <div className="mb-2 text-xs text-gray-400">
                                        Missing: <span className="text-red-300">{neededAreas.join(', ')}</span>
                                    </div>
                                    <button
                                        onClick={() => fetchOpenClasses(neededAreas[0])} // Just pick the first missing area for now
                                        disabled={loadingArea === neededAreas[0]}
                                        className="w-full py-2 px-3 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors flex items-center justify-center gap-2"
                                    >
                                        {loadingArea === neededAreas[0] ? (
                                            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        ) : isOpen ? 'Hide Classes' : `Find ${neededAreas[0]} Classes`}
                                    </button>
                                </div>
                            )}

                            {/* Expandable Open Classes List */}
                            {isOpen && (
                                <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar animate-fade-in text-left">
                                    {openClasses[neededAreas[0]]?.length === 0 ? (
                                        <p className="text-sm text-gray-500 italic">No open classes found.</p>
                                    ) : (
                                        openClasses[neededAreas[0]]?.map((cls: any, idx: number) => (
                                            <div key={idx} className="p-2 bg-gray-700/50 rounded text-sm hover:bg-gray-700 transition-colors border border-gray-600/30">
                                                <div className="flex justify-between font-medium text-blue-300">
                                                    <span>{cls.course_name}</span>
                                                    <span>{cls.open_seats} seats</span>
                                                </div>
                                                <div className="text-gray-400 text-xs mt-1 flex justify-between">
                                                    <span>{cls.days} {cls.start_time}-{cls.end_time}</span>
                                                    <span className="truncate max-w-[100px] text-right">{cls.instructor}</span>
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
                <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded text-red-300 text-sm">
                    {error}
                </div>
            )}
        </div>
    );
};

export default GeTracker;
