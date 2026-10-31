import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Activity,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Globe,
  HardDrive,
  RefreshCw,
  Server,
  Terminal,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { KpiStatCard } from '../components/ui/KpiStatCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { StatusIndicator } from '../components/ui/StatusIndicator';

export function SystemHealthPage() {
  const { healthData, isLoading, isError, clientLatencyMs, refetch } = useOutletContext();
  const [showRawJson, setShowRawJson] = useState(false);

  const db = healthData?.database;
  const sys = healthData?.system;
  const isHealthy = healthData?.status === 'healthy';
  const isDegraded = healthData?.status === 'degraded';

  const formatUptime = (seconds) => {
    if (!seconds && seconds !== 0) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins >= 60) {
      const hours = Math.floor(mins / 60);
      return `${hours}h ${mins % 60}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              System Health & Diagnostics
            </h2>
            <Badge
              variant={isHealthy ? 'success' : isDegraded ? 'warning' : 'danger'}
              size="default"
            >
              {healthData?.status ? healthData.status.toUpperCase() : isError ? 'OFFLINE' : 'CHECKING'}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Live operational status, PostgreSQL database connectivity, and backend diagnostics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowRawJson(!showRawJson)}
            icon={Terminal}
          >
            {showRawJson ? 'Hide Payload' : 'Inspect Raw JSON'}
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={refetch}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Run Health Probe
          </Button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiStatCard
          title="Overall Health"
          value={healthData?.status ? healthData.status.toUpperCase() : isError ? 'OFFLINE' : '...'}
          subtitle={isHealthy ? 'All services operational' : isDegraded ? 'Degraded/fallback active' : 'Backend unreachable'}
          icon={Activity}
          status={isHealthy ? 'healthy' : isDegraded ? 'degraded' : 'offline'}
          badgeText={healthData?.environment || 'DEV'}
        />

        <KpiStatCard
          title="Database Layer"
          value={db?.dialect ? db.dialect.toUpperCase() : 'N/A'}
          subtitle={db?.connected ? `Connected (${db.database_name})` : 'Disconnected'}
          icon={Database}
          status={db?.connected ? 'healthy' : 'offline'}
          badgeText={db?.connected ? `${db.latency_ms}ms ping` : 'Offline'}
        />

        <KpiStatCard
          title="Server Uptime"
          value={formatUptime(healthData?.uptime_seconds)}
          subtitle={healthData?.timestamp ? `Since ${new Date(healthData.timestamp).toLocaleTimeString()}` : '—'}
          icon={Clock}
          status={isHealthy ? 'healthy' : 'warning'}
          badgeText={`v${healthData?.version || '1.0'}`}
        />

        <KpiStatCard
          title="Client Roundtrip"
          value={clientLatencyMs !== null ? `${clientLatencyMs}ms` : '—'}
          subtitle="Direct Axios to FastAPI latency"
          icon={Zap}
          status={clientLatencyMs && clientLatencyMs < 100 ? 'healthy' : 'warning'}
          badgeText={clientLatencyMs && clientLatencyMs < 100 ? 'Fast' : 'Normal'}
        />
      </div>

      {/* Primary Diagnostic Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Database Connectivity Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  <span>Database Engine & Connection Pool</span>
                </CardTitle>
                <CardDescription>
                  SQLAlchemy 2.0 Async Session and driver connectivity parameters
                </CardDescription>
              </div>
              <Badge variant={db?.connected ? 'success' : 'danger'}>
                {db?.connected ? 'CONNECTED' : 'DISCONNECTED'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                <span className="text-xs font-medium text-slate-500">Active Dialect</span>
                <p className="mt-1 font-mono text-sm font-bold text-slate-900 uppercase">
                  {db?.dialect || 'None'}
                </p>
                <span className="text-[11px] text-slate-400">
                  {db?.dialect === 'postgresql'
                    ? 'Native PostgreSQL via asyncpg'
                    : 'Development SQLite fallback (aiosqlite)'}
                </span>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                <span className="text-xs font-medium text-slate-500">Database Name</span>
                <p className="mt-1 font-mono text-sm font-bold text-slate-900">
                  {db?.database_name || 'N/A'}
                </p>
                <span className="text-[11px] text-slate-400">Target storage schema</span>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                <span className="text-xs font-medium text-slate-500">Host Endpoint</span>
                <p className="mt-1 font-mono text-sm font-bold text-slate-900">
                  {db?.host || 'localhost'}:{db?.port || (db?.dialect === 'postgresql' ? 5432 : 'file')}
                </p>
                <span className="text-[11px] text-slate-400">Internal network address</span>
              </div>

              <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                <span className="text-xs font-medium text-slate-500">Probe Latency</span>
                <p className="mt-1 font-mono text-sm font-bold text-slate-900">
                  {db?.latency_ms !== undefined ? `${db.latency_ms} ms` : '—'}
                </p>
                <span className="text-[11px] text-slate-400">Execution time of SELECT 1</span>
              </div>
            </div>

            {db?.error_detail && (
              <div className="rounded-lg bg-amber-50 p-3 border border-amber-200">
                <p className="text-xs font-semibold text-amber-800">Connection Notice</p>
                <p className="mt-1 text-xs font-mono text-amber-700 break-all">{db.error_detail}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Host & Subsystem Status Matrix */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-4 w-4 text-blue-600" />
              <span>Platform Subsystems</span>
            </CardTitle>
            <CardDescription>Individual component readiness</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {healthData?.services ? (
              Object.entries(healthData.services).map(([service, state]) => (
                <div
                  key={service}
                  className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                >
                  <span className="text-xs font-medium capitalize text-slate-700">
                    {service.replace('_', ' ')}
                  </span>
                  <Badge
                    variant={state === 'operational' || state === 'ready' ? 'success' : 'warning'}
                    size="sm"
                  >
                    {state.toUpperCase()}
                  </Badge>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">No services telemetry received</p>
            )}

            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="flex justify-between text-xs text-slate-600">
                <span className="flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-slate-400" />
                  Host Platform:
                </span>
                <span className="font-mono text-slate-800">{sys?.platform || 'Windows'}</span>
              </div>

              <div className="flex justify-between text-xs text-slate-600">
                <span className="flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5 text-slate-400" />
                  Python Version:
                </span>
                <span className="font-mono text-slate-800">{sys?.python_version || '3.11+'}</span>
              </div>

              <div className="flex justify-between text-xs text-slate-600">
                <span className="flex items-center gap-1.5">
                  <HardDrive className="h-3.5 w-3.5 text-slate-400" />
                  CPU Cores:
                </span>
                <span className="font-mono text-slate-800">{sys?.cpu_count || 1} Cores</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Raw JSON Telemetry Inspector */}
      {showRawJson && (
        <Card className="border-navy-900/20 bg-slate-900 text-slate-100 shadow-xl">
          <CardHeader className="border-slate-800">
            <div className="flex items-center justify-between">
              <CardTitle className="text-white font-mono text-sm flex items-center gap-2">
                <Terminal className="h-4 w-4 text-emerald-400" />
                GET /api/v1/health Response Payload
              </CardTitle>
              <Badge variant="navy" className="border-slate-700 text-slate-300">
                JSON Contract
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="font-mono text-xs overflow-x-auto p-4 rounded bg-slate-950 text-emerald-400 leading-relaxed border border-slate-800">
              {JSON.stringify(healthData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default SystemHealthPage;

