import React from 'react';

const majors = [
  "Select a Major",
  "Computer Science",
  "Software Engineering",
  "Computer Engineering",
  "Data Science",
  "Electrical Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Chemical Engineering",
  "Bioengineering",
  "Business Administration",
  "Economics",
  "Psychology",
  "Art",
  "Music"
];

interface MajorDropdownProps {
  major: string;
  setMajor: (major: string) => void;
}

const MajorDropdown: React.FC<MajorDropdownProps> = ({ major, setMajor }) => {
  return (
    <div className="mb-6">
      <label htmlFor="major-select" className="block mb-3 font-medium">Select Your Major</label>
      <select 
        id="major-select" 
        className="w-full p-3 bg-gray-800 border border-gray-600 rounded text-white text-base focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent" 
        value={major} 
        onChange={(e) => setMajor(e.target.value)}
      >
        {majors.map((majorOption, index) => (
          <option key={index} value={majorOption === "Select a Major" ? "" : majorOption} className="bg-gray-800 text-white">{majorOption}</option>
        ))}
      </select>
    </div>
  );
};

export default MajorDropdown;
