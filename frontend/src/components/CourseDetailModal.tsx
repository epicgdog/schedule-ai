import React, { useEffect, useState } from 'react';
import Modal from './ui/Modal';
import { Book, GraduationCap, Clock, Loader2 } from 'lucide-react';

interface CourseDetails {
  course_name: string;
  description: string;
  units: string;
}

interface CourseDetailModalProps {
  courseCode: string | null;
  isOpen: boolean;
  onClose: () => void;
}

const CourseDetailModal: React.FC<CourseDetailModalProps> = ({ 
  courseCode, 
  isOpen, 
  onClose 
}) => {
  const [details, setDetails] = useState<CourseDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && courseCode) {
      const fetchDetails = async () => {
        setLoading(true);
        setError(null);
        try {
          const response = await fetch(`http://localhost:8000/api/course/${encodeURIComponent(courseCode)}`);
          if (!response.ok) throw new Error('Course not found');
          const data = await response.json();
          setDetails(data.data);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load course details');
        } finally {
          setLoading(false);
        }
      };
      fetchDetails();
    } else if (!isOpen) {
      // Clear details when closed to avoid flash of old content
      setDetails(null);
    }
  }, [isOpen, courseCode]);

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title={courseCode || 'Course Details'}
    >
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-gray-400 text-sm font-medium">Fetching details from SJSU Catalog...</p>
        </div>
      ) : error ? (
        <div className="py-12 text-center">
          <p className="text-red-400 font-bold mb-2">Error Loading Details</p>
          <p className="text-gray-500 text-sm">{error}</p>
        </div>
      ) : details ? (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="flex flex-col gap-4">
            <h3 className="text-2xl font-extrabold text-white leading-tight">
              {details.course_name}
            </h3>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-wider">
                <Clock className="w-3.5 h-3.5" />
                <span>{details.units} Units</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5 text-gray-400 text-xs font-bold uppercase tracking-wider">
                <GraduationCap className="w-3.5 h-3.5" />
                <span>Undergraduate</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-gray-100 font-bold uppercase tracking-widest text-[10px]">
              <Book className="w-3.5 h-3.5 text-blue-500" />
              <span>Catalog Description</span>
            </div>
            <div className="bg-black/20 rounded-2xl p-6 border border-white/5 shadow-inner">
              <p className="text-gray-300 leading-relaxed text-sm whitespace-pre-wrap">
                {details.description}
              </p>
            </div>
          </div>

          <div className="pt-4 flex gap-3">
            <button className="flex-1 py-3 px-6 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] active:scale-[0.98]">
              Add to Planned
            </button>
            <button 
              onClick={onClose}
              className="px-6 py-3 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-300 font-bold text-sm transition-all border border-white/5 active:scale-[0.98]"
            >
              Close
            </button>
          </div>
        </div>
      ) : null}
    </Modal>
  );
};

export default CourseDetailModal;
