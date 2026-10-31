import React, { useState, useEffect } from 'react';
import { RefreshCw, Search, Server } from 'lucide-react';
import Button from '../ui/Button';
import { StatusIndicator } from '../ui/StatusIndicator';
import { NotificationDropdown } from './NotificationDropdown';
import { UserProfileMenu } from './UserProfileMenu';
import { GlobalSearchModal } from './GlobalSearchModal';

export function Topbar({
  isBackendOnline,
  dbStatus,
  clientLatencyMs,
  isRefreshing,
  onRefresh,
}) {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Keyboard shortcut CMD+K or Ctrl+K to open search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 px-6 backdrop-blur shadow-sm">
        {/* Left Section: Global Search Bar */}
        <div className="flex items-center gap-4 flex-1 max-w-md">
          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2.5 w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-300 hover:bg-slate-100/70 transition-all text-left shadow-inner"
          >
            <Search className="h-4 w-4 text-slate-400" />
            <span className="flex-1">Search workforce, projects, skills...</span>
            <kbd className="hidden sm:inline-block rounded bg-white px-1.5 py-0.5 text-[10px] font-mono font-semibold text-slate-400 border border-slate-200 shadow-xs">
              Ctrl K
            </kbd>
          </button>
        </div>

        {/* Right Section: System Diagnostics, Notifications & Profile */}
        <div className="flex items-center gap-3">
          {/* Backend Connectivity Status Pill */}
          <div className="hidden lg:flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-1.5 text-xs">
            <StatusIndicator
              status={isBackendOnline ? 'healthy' : 'offline'}
              size="sm"
              pulse={isBackendOnline}
            />
            <span className="font-semibold text-slate-700">
              {isBackendOnline ? 'API Active' : 'API Offline'}
            </span>
            {clientLatencyMs !== null && isBackendOnline && (
              <span className="font-mono text-slate-400 border-l border-slate-200 pl-2">
                {clientLatencyMs}ms
              </span>
            )}
          </div>

          {/* Database Status Pill */}
          <div className="hidden xl:flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-1.5 text-xs">
            <Server className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-600">DB:</span>
            <span className="font-mono font-semibold text-slate-800 uppercase">
              {dbStatus || 'ONLINE'}
            </span>
          </div>

          {/* Live Refresh Trigger */}
          <Button
            size="sm"
            variant="ghost"
            onClick={onRefresh}
            isLoading={isRefreshing}
            icon={RefreshCw}
            className="h-8 w-8 p-0 text-slate-500 hover:text-slate-800"
            title="Refresh Diagnostics and Metrics"
          />

          {/* Notification Area */}
          <NotificationDropdown />

          <div className="h-6 w-px bg-slate-200" />

          {/* User Profile Menu */}
          <UserProfileMenu />
        </div>
      </header>

      {/* Global Search Dialog Modal */}
      <GlobalSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  );
}

export default Topbar;
