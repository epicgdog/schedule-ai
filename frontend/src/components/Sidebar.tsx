import React from 'react';
import { GitBranch, BarChart3, Calendar, Upload } from 'lucide-react';

export type TabId = 'tree' | 'ge' | 'schedule';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems = [
    { id: 'tree', label: 'Academic Tree', icon: GitBranch },
    { id: 'ge', label: 'GE Progress', icon: BarChart3 },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
  ] as const;

  return (
    <aside className="w-64 h-screen glass-panel border-r border-white/10 flex flex-col fixed left-0 top-0 z-20">
      <div className="p-6">
        <h2 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
          Schedule AI
        </h2>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive 
                  ? 'bg-white/10 text-blue-400 border border-white/5 shadow-lg' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-blue-400' : 'group-hover:text-white'}`} />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/5">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white transition-colors rounded-xl hover:bg-white/5">
          <Upload className="w-5 h-5" />
          <span className="font-medium text-sm">Upload History</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
