import React from 'react';
import type { Day } from "./ScheduleForm.tsx"

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] as const;

const timeLabels = Array.from({ length: 60 }, (_, i) => {
  const hour = 7 + Math.floor(i / 4);
  const minute = (i % 4) * 15;
  const isHourMark = minute === 0;

  let hourStr: string;
  if (hour === 12) {
    hourStr = "12";
  } else if (hour > 12) {
    hourStr = `${hour - 12}`;
  } else {
    hourStr = `${hour}`;
  }

  if (isHourMark) {
    const ampm = hour < 12 ? "AM" : "PM";
    return `${hourStr}:00 ${ampm}`;
  } else {
    return `${hourStr}:${minute.toString().padStart(2, '0')}`;
  }
});

interface TimeSelectorProps {
  selectedTimes: Record<Day, bigint>;
  setSelectedTimes: React.Dispatch<React.SetStateAction<Record<Day, bigint>>>
}

const TimeSelector: React.FC<TimeSelectorProps> = ({ selectedTimes, setSelectedTimes }) => {
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragDay, setDragDay] = React.useState<Day | null>(null);
  const [dragAction, setDragAction] = React.useState<'select' | 'deselect' | null>(null);

  const isSlotSelected = (day: Day, timeIndex: number) => {
    return (selectedTimes[day] & (1n << BigInt(timeIndex))) !== 0n;
  };

  const toggleSlot = (day: Day, timeIndex: number) => {
    setSelectedTimes((prev) => ({
      ...prev,
      [day]: prev[day] ^ (1n << BigInt(timeIndex))
    }));
  };

  const setSlot = (day: Day, timeIndex: number, selected: boolean) => {
    setSelectedTimes((prev) => {
      const newState = { ...prev };
      if (selected) {
        newState[day] = newState[day] | (1n << BigInt(timeIndex));
      } else {
        newState[day] = newState[day] & ~(1n << BigInt(timeIndex));
      }
      return newState;
    });
  };

  const handleSlotMouseDown = (day: Day, timeIndex: number) => {
    const wasSelected = isSlotSelected(day, timeIndex);
    setDragDay(day);
    setDragAction(wasSelected ? 'deselect' : 'select');
    setIsDragging(true);

    toggleSlot(day, timeIndex);
  };

  const handleSlotMouseEnter = (day: Day, timeIndex: number) => {
    if (!isDragging || dragDay !== day || dragAction === null) return;

    const shouldBeSelected = dragAction === 'select';
    const isSelected = isSlotSelected(day, timeIndex);

    if (isSelected !== shouldBeSelected) {
      setSlot(day, timeIndex, shouldBeSelected);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragDay(null);
    setDragAction(null);
  };

  return (
    <div
      className="mt-8"
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="grid grid-cols-6">
        {/* Header row */}
        <div></div>
        {days.map(day => (
          <div key={day} className="bg-gray-800 p-3 text-center font-semibold text-sm select-none">
            {day.slice(0, 3)}
          </div>
        ))}

        {/* Time rows - 60 rows, one per 15-minute slot */}
        {timeLabels.map((label, timeIndex) => {
          const quarterIndex = timeIndex % 4;
          const isHourMark = quarterIndex === 0;

          return (
            <React.Fragment key={timeIndex}>
              {/* Time label column */}
              <div
                className={`bg-gray-900 px-3 pr-4 py-0 text-right text-xs select-none ${
                  isHourMark ? 'font-bold text-gray-300' : 'text-gray-500'
                }`}
                style={{ height: '16px', lineHeight: '16px' }}
              >
                {label}
              </div>

              {/* Day columns */}
              {days.map(day => (
                <div
                  key={`${day}-${timeIndex}`}
                  onMouseDown={() => handleSlotMouseDown(day, timeIndex)}
                  onMouseEnter={() => handleSlotMouseEnter(day, timeIndex)}
                  className={`
                    h-4 cursor-pointer transition-colors duration-200 select-none border border-gray-700
                    ${isSlotSelected(day, timeIndex)
                      ? 'bg-white'
                      : 'bg-gray-800 hover:bg-gray-700'
                    }
                  `}
                  aria-label={`${day} at ${label}`}
                />
              ))}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default TimeSelector;
