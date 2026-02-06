import React, { useState, useRef } from 'react';

const MAX_FILE_SIZE = 1048576; // 1MB in bytes

const CourseInput: React.FC = () => {
  const [extractedText, setExtractedText] = useState<string | null>(null);
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
    setExtractedText(null);

    // Validate file type
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
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
        throw new Error(errorData.detail || 'Failed to process PDF');
      }

      const data = await response.json();
      setExtractedText(data.text);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setExtractedText(null);
    setFileName(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="mb-6">
      <label className="block mb-3 font-medium">Upload Your Transcript (PDF)</label>
      
      <input
        type="file"
        accept=".pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      {!extractedText && (
        <button
          type="button"
          onClick={handleButtonClick}
          disabled={isLoading}
          className="w-full p-4 bg-gray-800 border border-gray-600 rounded text-white text-base cursor-pointer transition-colors hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Processing...' : 'Choose PDF File'}
        </button>
      )}

      {fileName && !extractedText && !error && (
        <p className="mt-2 text-sm text-gray-400">Selected: {fileName}</p>
      )}

      {error && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}

      {extractedText && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">Extracted from: {fileName}</span>
            <button
              type="button"
              onClick={handleReset}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Upload different PDF
            </button>
          </div>
          <div className="w-full p-3 bg-gray-800 border border-gray-600 rounded text-white text-sm max-h-64 overflow-y-auto whitespace-pre-wrap">
            {extractedText}
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseInput;
