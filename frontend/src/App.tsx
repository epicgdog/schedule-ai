import React, { useState } from 'react';
import MajorDropdown from './components/MajorDropdown';
import CourseTree from './components/CourseTree';
import ElectiveList from './components/ElectiveList';
import DashboardLayout from './components/DashboardLayout';
import GeTracker from './components/GeTracker';
import type { TabId } from './components/Sidebar';
import { usePlanner } from './context/PlannerContext';

function App() {
  const { selectedPoid, setSelectedPoid } = usePlanner();
  const [activeTab, setActiveTab] = useState<TabId>('tree');

  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab}>
      <div className="space-y-8">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 glass-panel p-8 rounded-2xl border border-white/5 shadow-2xl">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Academic Planner</h1>
            <p className="text-gray-400 mt-1">Design your path at SJSU</p>
          </div>
          <div className="w-full md:w-72">
            <MajorDropdown selectedPoid={selectedPoid} onSelect={setSelectedPoid} />
          </div>
        </header>

        {selectedPoid && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            {activeTab === 'tree' && (
              <div className="space-y-8">
                <section className="glass-panel p-1 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
                  <CourseTree poid={selectedPoid} />
                </section>
                <section className="glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl">
                  <ElectiveList poid={selectedPoid} />
                </section>
              </div>
            )}

            {activeTab === 'ge' && (
              <section className="animate-in fade-in zoom-in-95 duration-500">
                <div className="glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl">
                  <GeTracker />
                </div>
              </section>
            )}

            {activeTab === 'schedule' && (
              <section className="animate-in fade-in zoom-in-95 duration-500">
                <div className="glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl text-center py-32">
                  <h2 className="text-2xl font-bold text-white mb-4">Schedule Builder</h2>
                  <p className="text-gray-400">Select your preferred times and generate optimized class sections.</p>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default App;
