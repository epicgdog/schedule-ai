import React from 'react';
import { GitBranch, BarChart3, Calendar, Upload, BookOpen, Search, Star, History, AlertTriangle } from 'lucide-react';
import TranscriptUploader from './TranscriptUploader';

export type TabId = 'tree' | 'ge' | 'schedule' | 'programs' | 'search' | 'ratings';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems = [
    { id: 'tree', label: 'Academic Tree', icon: GitBranch },
    { id: 'ge', label: 'GE Progress', icon: BarChart3 },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'programs', label: 'Programs', icon: BookOpen },
    { id: 'search', label: 'Course Search', icon: Search },
    { id: 'ratings', label: 'Instructor Ratings', icon: Star },
  ] as const;

  return (
    <aside className="w-64 h-screen glass-panel border-r border-white/10 flex flex-col fixed left-0 top-0 z-20">
      <div className="p-6">
        <h2 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
          Schedule AI
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar px-4 space-y-8 py-4">
        <div>
          <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Navigation</h3>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group ${
                    isActive 
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(37,99,235,0.1)]' 
                      : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4.5 h-4.5 transition-colors ${isActive ? 'text-blue-400' : 'group-hover:text-white'}`} />
                  <span className="font-medium text-sm">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div>
          <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Transcript Analysis</h3>
          <div className="space-y-1">
            <TranscriptUploader />
            <button className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-400 hover:text-white transition-colors rounded-xl hover:bg-white/5 border border-transparent">
              <History className="w-4.5 h-4.5" />
              <span className="font-medium text-sm">Course History</span>
            </button>
          </div>
        </div>

        <div>
          <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Planner</h3>
          <div className="space-y-1">
            <button className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-400 hover:text-white transition-colors rounded-xl hover:bg-white/5 border border-transparent">
              <BookOpen className="w-4.5 h-4.5" />
              <span className="font-medium text-sm">Planned Courses</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-400 hover:text-white transition-colors rounded-xl hover:bg-white/5 border border-transparent">
              <AlertTriangle className="w-4.5 h-4.5 text-yellow-500/70" />
              <span className="font-medium text-sm">Warnings</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-white/5 bg-black/20">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xs">
            SJ
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">SJSU Student</p>
            <p className="text-[10px] text-gray-500 truncate">Software Engineering</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
