import React, { useState } from 'react';

// Define the shape of our GE class data
interface GeClass {
    course_name: string;
    name?: string;
    code?: string;
    area: string;
    section_number?: number;
    class_number?: number;
    days?: string;
    start_time?: string;
    end_time?: string;
    instructor?: string;
    open_seats?: number;
}

interface GeTrackerProps {
    takenGeClasses: { name: string; area: string }[];
    neededGeAreas: string[];
    waivedGeAreas?: string[];
}

const GE_AREAS = ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C1/C2", "D", "E", "F"];

const GeTracker: React.FC<GeTrackerProps> = ({ takenGeClasses, neededGeAreas, waivedGeAreas = [] }) => {
    const [openClasses, setOpenClasses] = useState<Record<string, GeClass[]>>({});
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

    const getStatus = (area: string): 'completed' | 'waived' | 'missing' => {
        // If not in needed list AND is in waived list → waived by major
        // Handle D1 waiver covering D
        const isWaived = waivedGeAreas.includes(area) ||
            (area === 'D' && waivedGeAreas.includes('D1'));

        if (!neededGeAreas.includes(area) && isWaived) return 'waived';
        if (!neededGeAreas.includes(area)) return 'completed';
        return 'missing';
    };

    const getTakenClass = (area: string) => {
        return takenGeClasses.find(c => c.area === area);
    };

    return (
        <div className="w-full mt-8 p-6 bg-gray-900 rounded-lg border border-gray-700">
            <h2 className="text-2xl font-bold mb-6 text-white border-b border-gray-700 pb-2">GE Progress Tracker</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {GE_AREAS.map((area) => {
                    const status = getStatus(area);
                    const takenClass = getTakenClass(area);
                    const isOpen = expandedArea === area;

                    return (
                        <div
                            key={area}
                            className={`p-4 rounded-lg border transition-all ${status === 'completed'
                                ? 'bg-green-900/20 border-green-700/50'
                                : status === 'waived'
                                    ? 'bg-green-900/20 border-green-700/50'
                                    : 'bg-gray-800 border-gray-600 hover:border-blue-500'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="text-lg font-bold text-gray-200">Area {area}</span>
                                {status === 'completed' ? (
                                    <span className="px-2 py-1 text-xs font-semibold bg-green-500/20 text-green-400 rounded-full">
                                        Completed
                                    </span>
                                ) : status === 'waived' ? (
                                    <span className="px-2 py-1 text-xs font-semibold bg-purple-500/20 text-purple-400 rounded-full">
                                        Waived by Major
                                    </span>
                                ) : (
                                    <span className="px-2 py-1 text-xs font-semibold bg-red-500/20 text-red-400 rounded-full">
                                        Missing
                                    </span>
                                )}
                            </div>

                            {status === 'completed' && takenClass ? (
                                <div className="text-sm text-gray-400">
                                    <p className="font-medium text-gray-300">{takenClass.name}</p>
                                </div>
                            ) : status === 'waived' ? (
                                <div className="text-sm text-white mt-1">
                                    <p>Satisfied by major requirements</p>
                                </div>
                            ) : status === 'missing' ? (
                                <div className="mt-4">
                                    <button
                                        onClick={() => fetchOpenClasses(area)}
                                        disabled={loadingArea === area}
                                        className="w-full py-2 px-3 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors flex items-center justify-center gap-2"
                                    >
                                        {loadingArea === area ? (
                                            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        ) : isOpen ? 'Hide Classes' : 'Find Classes'}
                                    </button>
                                </div>
                            ) : null}

                            {/* Expandable Open Classes List */}
                            {isOpen && status === 'missing' && (
                                <div className="mt-4 space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
                                    {openClasses[area]?.length === 0 ? (
                                        <p className="text-sm text-gray-500 italic">No open classes found.</p>
                                    ) : (
                                        openClasses[area]?.map((cls, idx) => (
                                            <div key={idx} className="p-2 bg-gray-700/50 rounded text-sm hover:bg-gray-700 transition-colors">
                                                <div className="flex justify-between font-medium text-blue-300">
                                                    <span>{cls.course_name}</span>
                                                    <span>{cls.open_seats} seats</span>
                                                </div>
                                                <div className="text-gray-400 text-xs mt-1">
                                                    {cls.days} {cls.start_time}-{cls.end_time}
                                                </div>
                                                <div className="text-gray-500 text-xs truncate">
                                                    {cls.instructor}
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
