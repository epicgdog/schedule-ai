import React, { useEffect, useState } from 'react';
import MajorDropdown from './MajorDropdown';
import CourseInput from './CourseInput';
import TimeSelector from './TimeSelector';


// function parseScheduleList(selectedTimes : Set<string>) : Map<String, String> {
//   const timesArray = Array.from(selectedTimes);
//   const schedule = new Map(); // adding to a ma2p so all the times are grouped accordingly

//   timesArray.map((val, _) => {
//     const valArray = val.split("-");
//     const day = valArray[0];
//     const time = parseInt(valArray[1]);
    
//     if (schedule.has(day)){
//       schedule.get(day).push(time);
//     } else {
//       schedule.set(day, [time]);
//     }
//   })
//   console.log(schedule)
  
//   // condense each of the times basically and each fo the days has the availability
//   schedule.forEach( (val, key) => {
//     // key is the day, val is the times that are available
//     const times:number[] = val.sort();
//     let endingString = "";
//     let prevTime = -1;
//     let startIndex = 0;
//     let endIndex = 0;
//     times.map((val, index) => {
//       const num = val;
//       if (prevTime == -1 || (num - prevTime) == 1){ // change algorithm later
//         prevTime = num;
//         endIndex = index;
//       } else {
//         // chain is broken, add to endingString
//         endingString += `${times[startIndex]}-${num} `
//         startIndex = index + 1;
//         endIndex = startIndex;
//       }
      
//     })
    
//   })
  
//   console.log(schedule)
//   return schedule;
 
// }



export type Day = "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday" | "Sunday";
const DAYS: Day[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const initialState = Object.fromEntries( DAYS.map((day) => [day, 0n]) ) as Record<Day, bigint>
const ScheduleForm: React.FC = () => {
  const [step, setStep] = useState(1);
  const [major, setMajor] = useState('');
  const [courses, setCourses] = useState('');
  const [selectedTimes, setSelectedTimes] = useState<Record<Day, bigint>>(initialState);  

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  useEffect(()=> {
    
  }, [])

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
      courses: courses,
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
      <div className="w-full max-w-2xl p-10 border border-gray-700 rounded-lg bg-gray-900">
        <h1 className="text-3xl font-bold text-center mb-8">Class Scheduler</h1>
        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <MajorDropdown major={major} setMajor={setMajor} />
          )}
          {step === 2 && (
            <CourseInput courses={courses} setCourses={setCourses} />
          )}
          {step === 3 && (
            <>
              <TimeSelector selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes} />
           
            </>
          )}

          <div className="flex justify-between mt-8">
            {step > 1 && (
              <button type="button" className="px-8 py-3 border border-gray-600 rounded bg-gray-800 text-white cursor-pointer font-medium transition-colors hover:bg-gray-700" onClick={handleBack}>
                Back
              </button>
            )}
            {step < 3 && (
              <button type="button" className="ml-auto px-8 py-3 border border-gray-600 rounded bg-white text-black cursor-pointer font-medium transition-colors hover:bg-gray-200 disabled:bg-gray-600 disabled:text-gray-400 disabled:cursor-not-allowed" onClick={handleNext} disabled={step === 1 && !major}>
                Next
              </button>
            )}
            {step === 3 && (
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
