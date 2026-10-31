import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Tabs({ tabs = [], activeTab, onChange, className = '' }) {
  return (
    <div className={twMerge(clsx('flex border-b border-slate-200 overflow-x-auto no-scrollbar', className))}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={clsx(
              'group flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-semibold whitespace-nowrap transition-colors focus:outline-none',
              isActive
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800'
            )}
          >
            {Icon && (
              <Icon
                className={clsx(
                  'h-4 w-4 transition-colors',
                  isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'
                )}
              />
            )}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={clsx(
                  'ml-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold font-mono',
                  isActive ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default Tabs;
