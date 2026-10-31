import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Users,
  Briefcase,
  Calendar,
  GraduationCap,
  FolderGit2,
  TrendingUp,
  Layers,
  BrainCircuit,
  Sliders,
  Sparkles,
  Zap,
  SplitSquareVertical,
  AlertTriangle,
  CheckCircle,
  History,
  Shield,
  ChevronLeft,
  ChevronRight,
  BarChart3,
} from 'lucide-react';
import clsx from 'clsx';

export function Sidebar({ dbStatus = 'healthy', isBackendOnline = true }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navSections = [
    {
      title: 'Core Platform',
      items: [
        { name: 'Executive Dashboard', to: '/dashboard', icon: LayoutDashboard },
        { name: 'System Diagnostics', to: '/health', icon: Activity },
      ],
    },
    {
      title: 'Workforce',
      items: [
        { name: 'Employee Directory', to: '/employees', icon: Users },
        { name: 'Roles & Skills', to: '/roles-skills', icon: Briefcase },
        { name: 'Availability & Leave', to: '/availability', icon: Calendar },
        { name: 'Training Management', to: '/training', icon: GraduationCap },
      ],
    },
    {
      title: 'Planning & Capacity',
      items: [
        { name: 'Project Management', to: '/projects', icon: FolderGit2 },
        { name: 'Demand Forecast', to: '/forecast', icon: TrendingUp },
        { name: 'Resource Allocations', to: '/allocations', icon: Layers },
        { name: 'Skill Gap Analysis', to: '/skill-gaps', icon: BrainCircuit },
        { name: 'Workforce Utilization', to: '/utilization', icon: Sliders },
      ],
    },
    {
      title: 'AI Intelligence',
      items: [
        { name: 'Recommendations', to: '/recommendations', icon: Sparkles },
        { name: 'Resource Optimization', to: '/optimization', icon: Zap },
        { name: 'Scenario Planning', to: '/scenarios', icon: SplitSquareVertical },
      ],
    },
    {
      title: 'Governance & Quality',
      items: [
        { name: 'Exception Monitoring', to: '/exceptions', icon: AlertTriangle, badge: 'Anomalies' },
        { name: 'Quality & Evaluation', to: '/quality', icon: CheckCircle },
        { name: 'Audit History', to: '/audit', icon: History },
        { name: 'Administration', to: '/admin', icon: Shield },
      ],
    },
  ];

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-30 flex flex-col bg-navy-900 text-slate-300 shadow-xl border-r border-navy-800 select-none transition-all duration-200',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-navy-800/80 bg-navy-950/60">
        <NavLink to="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white font-bold shadow-md shadow-blue-500/20">
            <BarChart3 className="h-5 w-5" />
          </div>
          {!isCollapsed && (
            <div className="truncate">
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-white tracking-tight">WorkforceIQ</span>
                <span className="rounded bg-blue-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-blue-300">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 truncate">Enterprise Intelligence</p>
            </div>
          )}
        </NavLink>

        {/* Collapse Toggle Button */}
        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 no-scrollbar">
        {navSections.map((section, idx) => (
          <div key={idx}>
            {!isCollapsed && (
              <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400/70 truncate">
                {section.title}
              </p>
            )}
            <nav className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    title={isCollapsed ? item.name : undefined}
                    className={({ isActive }) =>
                      clsx(
                        'group flex items-center rounded-lg px-3 py-2 text-xs font-medium transition-all relative',
                        isActive
                          ? 'bg-blue-600 text-white shadow-sm font-semibold'
                          : 'text-slate-300 hover:bg-navy-800/80 hover:text-white',
                        isCollapsed ? 'justify-center' : 'justify-between'
                      )
                    }
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon className="h-4 w-4 shrink-0 transition-transform group-hover:scale-105" />
                      {!isCollapsed && <span className="truncate">{item.name}</span>}
                    </div>

                    {!isCollapsed && item.badge && (
                      <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-bold text-amber-300 uppercase tracking-wider">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      {!isCollapsed && (
        <div className="p-3 border-t border-navy-800/80 bg-navy-950/40 text-[11px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={clsx(
                'h-2 w-2 rounded-full',
                isBackendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
              )}
            />
            <span className="font-mono">{isBackendOnline ? 'SYSTEM READY' : 'OFFLINE'}</span>
          </div>
          <span className="font-mono text-[10px] text-slate-500">v1.0.0</span>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
