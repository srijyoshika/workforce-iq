import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import Breadcrumbs from './Breadcrumbs';
import ConnectionBanner from '../feedback/ConnectionBanner';
import { useHealthCheck } from '../../hooks/useHealthCheck';

export function AppLayout() {
  const {
    healthData,
    isLoading,
    isError,
    clientLatencyMs,
    refetch,
  } = useHealthCheck({ autoPoll: true, pollInterval: 20000 });

  const isBackendOnline = !isError && healthData !== null;
  const isDegraded = healthData?.status === 'degraded';
  const dbStatus = healthData?.database?.dialect || (isBackendOnline ? 'connected' : 'offline');

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Fixed Deep Navy Navigation Sidebar */}
      <Sidebar
        dbStatus={healthData?.database?.status || 'disconnected'}
        isBackendOnline={isBackendOnline}
      />

      {/* Main Content Area */}
      <div className="flex-1 pl-64 flex flex-col min-h-screen transition-all duration-200">
        <Topbar
          isBackendOnline={isBackendOnline}
          dbStatus={dbStatus}
          clientLatencyMs={clientLatencyMs}
          isRefreshing={isLoading}
          onRefresh={refetch}
        />

        <ConnectionBanner
          isConnected={isBackendOnline}
          isDegraded={isDegraded}
          isError={isError}
          onRetry={refetch}
          isRetrying={isLoading}
        />

        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Breadcrumbs />
          <Outlet context={{ healthData, isLoading, isError, clientLatencyMs, refetch }} />
        </main>

        {/* Enterprise Platform Footer */}
        <footer className="border-t border-slate-200/80 bg-white py-4 px-6 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>
              <span className="font-semibold text-slate-700">WorkforceIQ</span> — AI-Powered Workforce Demand Forecasting & Skill Gap Intelligence Platform
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              FastAPI • SQLAlchemy 2.x • PostgreSQL • React 19 • Tailwind CSS • Recharts
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default AppLayout;
