import React, { useState, useEffect, useCallback } from 'react';
import {
  History,
  Shield,
  Filter,
  RefreshCw,
  User,
  Clock,
  Layers,
  CheckCircle,
} from 'lucide-react';
import { intelligenceApi } from '../api/intelligence';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export function AuditHistoryPage() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAuditEvents = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await intelligenceApi.listAuditEvents({
        page,
        page_size: pageSize,
        action: actionFilter,
      });
      setEvents(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load audit events:', err);
      setEvents([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, actionFilter]);

  useEffect(() => {
    fetchAuditEvents();
  }, [fetchAuditEvents]);

  const columns = [
    {
      key: 'id',
      header: 'Event ID & Time',
      cell: (row) => (
        <div>
          <span className="font-mono font-bold text-slate-900 text-xs">{row.business_id || row.id}</span>
          <div className="text-[10px] font-mono text-slate-400">
            {new Date(row.created_at).toLocaleString()}
          </div>
        </div>
      ),
    },
    {
      key: 'actor',
      header: 'Actor / User Identity',
      cell: (row) => (
        <div className="flex items-center gap-1.5 font-medium text-slate-800 text-xs">
          <User className="h-3.5 w-3.5 text-slate-400" />
          <span>{row.actor_id || 'System Service'}</span>
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Operational Action',
      cell: (row) => (
        <Badge
          variant={
            row.action === 'APPROVE'
              ? 'success'
              : row.action === 'REJECT'
              ? 'danger'
              : row.action === 'SIMULATE'
              ? 'purple'
              : row.action === 'ALLOCATE'
              ? 'teal'
              : 'navy'
          }
        >
          {row.action}
        </Badge>
      ),
    },
    {
      key: 'entity',
      header: 'Target Entity Reference',
      cell: (row) => (
        <div className="font-mono text-xs">
          <span className="text-slate-500">{row.entity_type}: </span>
          <span className="font-semibold text-slate-800">{row.entity_id}</span>
        </div>
      ),
    },
    {
      key: 'payload',
      header: 'Audit Trail Details',
      cell: (row) => {
        const p = row.payload || {};
        return (
          <span className="text-slate-600 line-clamp-1 max-w-sm text-xs font-mono">
            {p.reason || p.name || p.details || JSON.stringify(p)}
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Audit Trail & Governance Log
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Immutable log of all administrative actions, scenario simulations, allocation updates, and recommendation approvals.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAuditEvents}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh Log
          </Button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={events}
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
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Operational Actions</option>
            <option value="SIMULATE">SIMULATE</option>
            <option value="ALLOCATE">ALLOCATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="APPROVE">APPROVE</option>
            <option value="REJECT">REJECT</option>
            <option value="DELETE">DELETE</option>
          </select>
        }
      />
    </div>
  );
}

export default AuditHistoryPage;
