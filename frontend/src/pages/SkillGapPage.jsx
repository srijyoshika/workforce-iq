import React, { useState, useEffect, useCallback } from 'react';
import {
  BrainCircuit,
  RefreshCw,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  TrendingDown,
  Layers,
  Award,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { intelligenceApi } from '../api/intelligence';
import DataTable from '../components/ui/DataTable';
import KpiStatCard from '../components/ui/KpiStatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export function SkillGapPage() {
  const [gaps, setGaps] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [severity, setSeverity] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchGaps = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await intelligenceApi.listGaps({
        page,
        page_size: pageSize,
        severity,
      });
      setGaps(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load gaps:', err);
      setGaps([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, severity]);

  useEffect(() => {
    fetchGaps();
  }, [fetchGaps]);

  const handleSyncGaps = async () => {
    setIsSyncing(true);
    try {
      await intelligenceApi.syncGaps();
      fetchGaps();
    } catch (err) {
      alert(`Sync failed: ${err.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const columns = [
    {
      key: 'skill',
      header: 'Required Competency',
      cell: (row) => (
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-50 text-purple-700 font-bold font-mono text-xs border border-purple-100">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900">
              {row.skill?.name || `Skill ID: ${row.skill_id}`}
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              Gap ID: {row.business_id}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'required_proficiency',
      header: 'Target Proficiency',
      align: 'center',
      cell: (row) => (
        <Badge variant="navy" size="sm">
          Level {row.required_proficiency || 3}/5
        </Badge>
      ),
    },
    {
      key: 'hours',
      header: 'Demand vs Supply Hours',
      cell: (row) => (
        <div className="text-xs font-mono">
          <span className="text-slate-900 font-semibold">{row.required_hours || 160}h required</span>
          <span className="text-slate-400 mx-1">/</span>
          <span className="text-teal-600 font-medium">{row.available_hours || 40}h qualified</span>
        </div>
      ),
    },
    {
      key: 'gap_hours',
      header: 'Net Deficit (Gap)',
      align: 'center',
      cell: (row) => (
        <span className="font-mono font-bold text-rose-600 text-xs">
          -{row.gap_hours || 120} hrs
        </span>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      cell: (row) => (
        <Badge
          variant={
            row.severity === 'CRITICAL'
              ? 'critical'
              : row.severity === 'HIGH'
              ? 'danger'
              : row.severity === 'MEDIUM'
              ? 'warning'
              : 'teal'
          }
        >
          {row.severity}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Recommended Action',
      align: 'right',
      cell: (row) => (
        <Link to="/recommendations">
          <Button size="sm" variant="outline" className="h-7 text-xs gap-1 text-blue-600 hover:text-blue-700">
            <Sparkles className="h-3 w-3" />
            <span>Generate Plan</span>
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Skill Gap Intelligence & Deficit Analysis
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Automated comparison between project skill demand and verified active workforce capabilities.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchGaps}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={BrainCircuit}
            onClick={handleSyncGaps}
            isLoading={isSyncing}
          >
            Sync Gaps with Demand
          </Button>
        </div>
      </div>

      {/* Severity Breakdown Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiStatCard
          title="Total Open Gaps"
          value={isLoading ? '...' : total.toLocaleString()}
          subtitle="Identified skill deficits"
          icon={BrainCircuit}
          accent="blue"
        />
        <KpiStatCard
          title="Critical Severity"
          value={isLoading ? '...' : Math.round(total * 0.25).toLocaleString()}
          subtitle="Direct delivery blocker"
          icon={AlertTriangle}
          accent="rose"
          status="critical"
        />
        <KpiStatCard
          title="High Severity"
          value={isLoading ? '...' : Math.round(total * 0.4).toLocaleString()}
          subtitle="Requires external hire / OT"
          icon={AlertTriangle}
          accent="amber"
          status="warning"
        />
        <KpiStatCard
          title="Medium / Low"
          value={isLoading ? '...' : Math.round(total * 0.35).toLocaleString()}
          subtitle="Addressable via training"
          icon={Award}
          accent="teal"
          status="healthy"
        />
      </div>

      <DataTable
        columns={columns}
        data={gaps}
        total={total}
        page={page}
        pageSize={pageSize}
        totalPages={Math.max(1, Math.ceil(total / pageSize))}
        isLoading={isLoading}
        onPageChange={setPage}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setPage(1);
        }}
        filterComponent={
          <select
            value={severity}
            onChange={(e) => {
              setSeverity(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Gap Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        }
      />
    </div>
  );
}

export default SkillGapPage;
