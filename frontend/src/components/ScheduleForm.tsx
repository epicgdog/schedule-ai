import React, { useState } from 'react';

import CourseInput from './CourseInput';
import TimeSelector from './TimeSelector';
import GeTracker from './GeTracker';

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
  const [geData, setGeData] = useState<GeAnalysisData | null>(null);
  const [selectedTimes, setSelectedTimes] = useState<Record<Day, bigint>>(initialState);

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
      const response = await fetch('http://localhost:8000/api/schedule', {
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
      <div className="w-full max-w-4xl p-10 border border-gray-700 rounded-lg bg-gray-900">
        <h1 className="text-3xl font-bold text-center mb-8">Class Scheduler</h1>
        <form onSubmit={handleSubmit}>
          {/* {step === 1 && (
            <MajorDropdown major={major} setMajor={setMajor} />
          )} */}
          {step === 1 && (
            <>
              <CourseInput onAnalysisComplete={handleAnalysisComplete} />
              {geData && (
                <div className="mt-8 animate-fade-in">
                  <GeTracker geCourses={geData.GE_Courses || {}} />

                  {/* Summary Section */}
                  <div className="mt-6 p-4 rounded bg-gray-800 border border-gray-700">
                    <h3 className="text-xl font-semibold mb-2 text-blue-400">Analysis Summary</h3>
                    <p>Major Detected: <span className="font-bold text-white">{geData.Major}</span></p>
                    <p>Name: <span className="font-bold text-white">{geData.Name}</span></p>
                  </div>
                </div>
              )}
            </>
          )}
          {step === 2 && (
            <>
              <TimeSelector selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes} />

            </>
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
