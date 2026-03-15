import React, { useState, useRef } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { usePlanner } from '../context/PlannerContext';

const MAX_FILE_SIZE = 1048576; // 1MB

const TranscriptUploader: React.FC = () => {
  const { setCourseHistory, setSelectedPoid } = usePlanner();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);

    // The original code checks for application/vnd.ms-excel specifically
    if (file.size > MAX_FILE_SIZE) {
      setError('File must be less than 1MB');
      return;
    }

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
        throw new Error(errorData.detail || 'Failed to process transcript');
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      let parsedData;
      try {
        if (typeof data.text === 'string') {
          parsedData = JSON.parse(data.text);
        } else {
          parsedData = data.text;
        }
      } catch (e) {
        throw new Error("Failed to parse transcript analysis results.");
      }

      if (!parsedData) {
        throw new Error("No analysis data received from server.");
      }

      // Update global state
      setCourseHistory(parsedData);
      if (parsedData.POID) {
        setSelectedPoid(String(parsedData.POID));
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
      // Reset input so the same file can be selected again
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      <input
        type="file"
        accept=".xls,.xlsx"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        data-testid="file-input"
      />

      <button
        onClick={handleButtonClick}
        disabled={isLoading}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-400 hover:text-white transition-all duration-200 rounded-xl hover:bg-white/5 group border border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <Loader2 className="w-4.5 h-4.5 animate-spin text-blue-400" />
        ) : (
          <Upload className="w-4.5 h-4.5 group-hover:text-blue-400 transition-colors" />
        )}
        <span className="font-medium text-sm">
          {isLoading ? 'Processing...' : 'Upload Record'}
        </span>
      </button>

      {error && (
        <p className="mt-2 px-4 text-[10px] text-red-400 leading-tight">{error}</p>
      )}
    </div>
  );
};

export default TranscriptUploader;
