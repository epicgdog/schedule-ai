import React, { useState } from 'react';
import MajorDropdown from './components/MajorDropdown';
import CourseTree from './components/CourseTree';
import ElectiveList from './components/ElectiveList';
import DashboardLayout from './components/DashboardLayout';
import { TabId } from './components/Sidebar';

function App() {
  const [selectedPoid, setSelectedPoid] = useState<string>('13772'); // Default to CS BS
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
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {activeTab === 'tree' && (
              <section className="glass-panel p-1 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
                <CourseTree poid={selectedPoid} />
              </section>
            )}

            {activeTab === 'ge' && (
              <section className="animate-in fade-in zoom-in-95 duration-500">
                <div className="glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl">
                  <h2 className="text-2xl font-bold text-white mb-6">General Education Progress</h2>
                  <p className="text-gray-400 mb-8">Visualization of your GE requirements based on common patterns.</p>
                  <div className="text-center py-20 text-gray-500 italic border border-dashed border-white/10 rounded-2xl">
                    GE Tracker Integration coming in Phase 3
                  </div>
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

            {/* Always show electives if they exist for the major? Or keep separate? */}
            {/* For now, show them below the tree in the tree view */}
            {activeTab === 'tree' && (
              <section className="glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl">
                <ElectiveList poid={selectedPoid} />
              </section>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default App;
