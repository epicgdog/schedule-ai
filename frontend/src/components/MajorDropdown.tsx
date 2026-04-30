import React, { useEffect, useState } from 'react';

interface Program {
  poid: string;
  program_name: string;
}

interface MajorDropdownProps {
  selectedPoid: string;
  onSelect: (poid: string) => void;
}

const MajorDropdown: React.FC<MajorDropdownProps> = ({ selectedPoid, onSelect }) => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPrograms() {
      try {
        const response = await fetch('/api/programs');
        if (!response.ok) throw new Error('Failed to fetch programs');
        const data = await response.json();
        setPrograms(data.data || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchPrograms();
  }, []);

  if (loading) return <div className="text-gray-400 mb-6">Loading majors...</div>;
  if (error) return <div className="text-red-400 mb-6">Error: {error}</div>;

  return (
    <div className="mb-6">
      <label htmlFor="major-select" className="block mb-3 font-medium text-white">Select Your Major</label>
      <select 
        id="major-select" 
        className="w-full p-3 bg-gray-800 border border-gray-600 rounded text-white text-base focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent" 
        value={selectedPoid} 
        onChange={(e) => onSelect(e.target.value)}
      >
        <option value="" className="bg-gray-800 text-white">Select a Major</option>
        {programs.map((prog) => (
          <option key={prog.poid} value={prog.poid} className="bg-gray-800 text-white">
            {prog.program_name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default MajorDropdown;
