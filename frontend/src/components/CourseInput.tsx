import React from 'react';

interface CourseInputProps {
  courses: string;
  setCourses: (courses: string) => void;
}

const CourseInput: React.FC<CourseInputProps> = ({ courses, setCourses }) => {
  return (
    <div className="mb-6">
      <label htmlFor="course-input" className="block mb-3 font-medium">Enter Your Courses</label>
      <textarea
        id="course-input"
        className="w-full p-3 bg-gray-800 border border-gray-600 rounded text-white text-base focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent resize-none"
        placeholder="e.g., CS151, ENGR100W, MATH129A"
        rows={4}
        value={courses}
        onChange={(e) => setCourses(e.target.value)}
      />
    </div>
  );
};

export default CourseInput;
