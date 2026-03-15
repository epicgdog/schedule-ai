import React from 'react';
import Sidebar, { TabId } from './Sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  children, 
  activeTab, 
  onTabChange 
}) => {
  return (
    <div className="flex min-h-screen bg-gray-950 text-gray-100 overflow-hidden">
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      
      <main className="flex-1 ml-64 min-h-screen relative overflow-y-auto">
        {/* Decorative background glow */}
        <div className="fixed top-0 right-0 w-full h-full pointer-events-none overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full" />
        </div>

        <div className="max-w-7xl mx-auto p-8 relative z-10">
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
