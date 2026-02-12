import React, { useState, useRef } from 'react';

const MAX_FILE_SIZE = 1048576; // 1MB in bytes

interface CourseInputProps {
  onAnalysisComplete: (data: any) => void;
}

const CourseInput: React.FC<CourseInputProps> = ({ onAnalysisComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset states
    setError(null);

    if (file.type != "application/vnd.ms-excel") {
      setError('Please upload a Excel file');
      return;
    }
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError('File must be less than 1MB');
      return;
    }

    setFileName(file.name);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/generate_classes', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process Excel');
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Parse the nested JSON string from the "text" field
      let parsedData;
      try {
        if (typeof data.text === 'string') {
          parsedData = JSON.parse(data.text);
        } else {
          parsedData = data.text;
        }
      } catch (e) {
        console.error("Failed to parse inner JSON", data.text);
        throw new Error("Failed to parse transcript analysis results.");
      }

      if (!parsedData) {
        throw new Error("No analysis data received from server.");
      }

      onAnalysisComplete(parsedData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mb-6">
      <label className="block mb-3 font-medium">Upload Your Transcript (Excel)</label>

      <input
        type="file"
        accept=".xls"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      <button
        type="button"
        onClick={handleButtonClick}
        disabled={isLoading}
        className="w-full p-4 bg-gray-800 border border-gray-600 rounded text-white text-base cursor-pointer transition-colors hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Processing Transcript...' : fileName ? `Change File (${fileName})` : 'Upload Your Course History (.xls/.xlsx)'}
      </button>

      {error && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};

export default CourseInput;
