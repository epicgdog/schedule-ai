import React from 'react';
import { X } from 'lucide-react';
import GlassPanel from './GlassPanel';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-in fade-in duration-300"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <GlassPanel className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col rounded-3xl border-white/10 shadow-2xl animate-in zoom-in-95 fade-in duration-300">
        <header className="p-6 flex items-center justify-between border-b border-white/5">
          <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </header>
        
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {children}
        </div>
      </GlassPanel>
    </div>
  );
};

export default Modal;
