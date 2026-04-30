import React, { useState } from 'react';

import CourseInput from './CourseInput';
import TimeSelector from './TimeSelector';
import GeTracker from './GeTracker';
import CourseTree from './CourseTree';

interface GeAnalysisData {
  Name: string;
  Major: string;
  GE_Courses: Record<string, { Areas: string[]; Units: number; Courses: string[] }>;
  Major_Courses: Record<string, any>;
}

export type Day = "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday" | "Sunday";
const DAYS: Day[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const initialState = Object.fromEntries(DAYS.map((day) => [day, 0n])) as Record<Day, bigint>
const ScheduleForm: React.FC = () => {
  const [step, setStep] = useState(1);
  const [major, setMajor] = useState('');
  const [poid, setPoid] = useState('13772');
  const [geData, setGeData] = useState<GeAnalysisData | null>(null);
  const [selectedTimes, setSelectedTimes] = useState<Record<Day, bigint>>(initialState);
  const [activeTab, setActiveTab] = useState<'schedule' | 'ge-tracker' | 'major-tree' | 'more'>('schedule');

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleAnalysisComplete = (data: GeAnalysisData) => {
    console.log("Analysis complete:", data);
    setGeData(data);
    if (data.Major) setMajor(data.Major);

    const maybePoid = (data as { POID?: string | number }).POID;
    if (maybePoid !== undefined && maybePoid !== null && String(maybePoid).trim()) {
      setPoid(String(maybePoid));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Check if any time slots are selected
    const hasSelection = Object.values(selectedTimes).some(dayBits => dayBits > 0n);
    if (!hasSelection) {
      alert('Please select at least one time slot');
      return;
    }

    const scheduleData = {
      major: major,
      courses: '',
      schedule: JSON.stringify(selectedTimes, (_key, value) => typeof value === 'bigint' ? value.toString() : value),
    };

    try {
      console.log('Submitting schedule data:', scheduleData);
      const response = await fetch('/api/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleData),
      });

      const result = await response.json();
      console.log('Server response:', response.status, result);

      if (response.ok) {
        console.log('Schedule submitted successfully:', result);
        alert('Schedule submitted!');
      } else {
        console.error('Failed to submit schedule:', result);
        alert(`Failed to submit schedule: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error submitting schedule:', error);
      alert(`An error occurred: ${error}`);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
      <div className="w-full max-w-[95%]  p-10 border border-gray-700 rounded-lg bg-gray-900">
        <h1 className="text-3xl font-bold text-center mb-8">Class Scheduler</h1>
        <form onSubmit={handleSubmit}>
          {/* {step === 1 && (
            <MajorDropdown major={major} setMajor={setMajor} />
          )} */}
          {step === 1 && (
            <>
              <CourseInput onAnalysisComplete={handleAnalysisComplete} />
              {geData && handleNext()}
            </>
          )}
          {step === 2 && (
            <div className="flex flex-col h-full">
              {/* Navigation Bar */}
              <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg mb-6">
                <button
                  type="button"
                  onClick={() => setActiveTab('schedule')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${activeTab === 'schedule'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                >
                  Schedule
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('ge-tracker')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${activeTab === 'ge-tracker'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                >
                  GE Tracker
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('major-tree')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${activeTab === 'major-tree'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                >
                  Major Tree
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('more')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${activeTab === 'more'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                >
                  More
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto">
                {activeTab === 'schedule' && (
                  <TimeSelector selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes} />
                )}

                {activeTab === 'ge-tracker' && (
                  <div className="animate-fade-in">
                    {geData ? (
                      <GeTracker geCourses={geData.GE_Courses || {}} />
                    ) : (
                      <div className="text-center text-gray-400 py-10">
                        <p>No GE data available. Please complete Step 1 first.</p>
                      </div>
                    )}

                  </div>
                )}

                {activeTab === 'major-tree' && (
                  <div className="p-4 border border-gray-700 rounded-lg bg-gray-900/60">
                    <div className="mb-4 flex items-center gap-3">
                      <label htmlFor="poid-input" className="text-sm text-gray-300">Program POID</label>
                      <input
                        id="poid-input"
                        value={poid}
                        onChange={(e) => setPoid(e.target.value)}
                        placeholder="e.g. 13772"
                        className="w-40 px-3 py-1.5 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                      />
                    </div>
                    <CourseTree poid={poid} />
                  </div>
                )}

                {activeTab === 'more' && (
                  <div className="flex flex-col items-center justify-center py-20 text-gray-400 border border-dashed border-gray-700 rounded-lg">
                    <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <title>More Icon</title>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
                    </svg>
                    <h3 className="text-xl font-medium mb-2">More Features</h3>
                    <p>Additional tools and views will appear here.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex justify-between mt-8 sticky bottom-0 bg-gray-900 py-4 border-t border-gray-800">
            {step > 1 && (
              <button type="button" className="px-8 py-3 border border-gray-600 rounded bg-gray-800 text-white cursor-pointer font-medium transition-colors hover:bg-gray-700" onClick={handleBack}>
                Back
              </button>
            )}
            {step < 2 && (
              <button type="button" className="ml-auto px-8 py-3 border border-gray-600 rounded bg-white text-black cursor-pointer font-medium transition-colors hover:bg-gray-200 disabled:bg-gray-600 disabled:text-gray-400 disabled:cursor-not-allowed" onClick={handleNext} disabled={step === 1 && !major}>
                Next
              </button>
            )}
            {step === 2 && (
              <button type="submit" className="w-full py-4 bg-white text-black border-none rounded font-semibold text-lg cursor-pointer transition-colors hover:bg-gray-200">
                Generate Schedule
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScheduleForm;
