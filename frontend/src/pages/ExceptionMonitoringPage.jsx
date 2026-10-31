import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Filter,
  ShieldAlert,
  Search,
  ExternalLink,
  Layers,
  Award,
  Copy,
  Clock,
} from 'lucide-react';
import { intelligenceApi } from '../api/intelligence';
import DataTable from '../components/ui/DataTable';
import KpiStatCard from '../components/ui/KpiStatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Select from '../components/ui/Select';

export function ExceptionMonitoringPage() {
  const [issues, setIssues] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [issueType, setIssueType] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  // Resolution Modal
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('RESOLVED');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchIssues = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await intelligenceApi.listIssues({
        page,
        page_size: pageSize,
        severity,
        status,
        issue_type: issueType,
      });
      setIssues(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load issues:', err);
      setIssues([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, severity, status, issueType]);

  useEffect(() => {
    fetchIssues();
  }, [fetchIssues]);

  const handleRunScan = async () => {
    setIsScanning(true);
    try {
      const res = await intelligenceApi.runRiskScan();
      alert(`Anomaly scan completed! Detected ${res.total_risks_detected} anomalies across the workforce.`);
      fetchIssues();
    } catch (err) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedIssue) return;
    setIsSubmitting(true);
    try {
      await intelligenceApi.updateIssue(selectedIssue.id, {
        status: newStatus,
        resolved_at: newStatus === 'RESOLVED' ? new Date().toISOString() : null,
      });
      setIsResolveModalOpen(false);
      fetchIssues();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getIssueTypeBadge = (type) => {
    switch (type) {
      case 'OVERALLOCATION':
        return <Badge variant="critical">OVERALLOCATION</Badge>;
      case 'STALE_SKILL':
        return <Badge variant="warning">STALE_SKILL</Badge>;
      case 'DUPLICATE_DEMAND':
        return <Badge variant="primary">DUPLICATE_DEMAND</Badge>;
      case 'OVERLAPPING_ALLOCATION':
        return <Badge variant="danger">OVERLAPPING_ALLOCATION</Badge>;
      default:
        return <Badge variant="default">{type}</Badge>;
    }
  };

  const columns = [
    {
      key: 'title',
      header: 'Anomaly Description',
      cell: (row) => (
        <div className="space-y-0.5">
          <div className="font-semibold text-slate-900 flex items-center gap-2">
            <span>{row.title}</span>
            <span className="font-mono text-[10px] text-slate-400">({row.business_id})</span>
          </div>
          <p className="text-xs text-slate-500 line-clamp-1 max-w-lg">{row.description}</p>
        </div>
      ),
    },
    {
      key: 'issue_type',
      header: 'Mandatory Anomaly Category',
      cell: (row) => getIssueTypeBadge(row.issue_type),
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
              : 'default'
          }
        >
          {row.severity}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      cell: (row) => (
        <Badge
          variant={
            row.status === 'RESOLVED'
              ? 'success'
              : row.status === 'IN_PROGRESS'
              ? 'primary'
              : 'warning'
          }
          size="sm"
        >
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'detected_at',
      header: 'Detected',
      cell: (row) => (
        <span className="text-[11px] font-mono text-slate-500">
          {new Date(row.detected_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right',
      cell: (row) => (
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs px-2"
          onClick={() => {
            setSelectedIssue(row);
            setNewStatus(row.status === 'OPEN' ? 'RESOLVED' : row.status);
            setIsResolveModalOpen(true);
          }}
        >
          Update Status
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Exception & Anomaly Monitoring
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Real-time detection of overallocation, stale certifications, duplicate demand, and overlapping assignments.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchIssues}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={ShieldAlert}
            onClick={handleRunScan}
            isLoading={isScanning}
          >
            Run Anomaly Scan
          </Button>
        </div>
      </div>

      {/* 4 Anomaly KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiStatCard
          title="Overallocation Exceptions"
          value="4 Active"
          subtitle="Hours > 100% capacity"
          icon={Clock}
          accent="rose"
          status="warning"
        />
        <KpiStatCard
          title="Stale Skill Profiles"
          value="7 Expired"
          subtitle="Verification > 365 days"
          icon={Award}
          accent="amber"
          status="warning"
        />
        <KpiStatCard
          title="Duplicate Demand"
          value="2 Duplicates"
          subtitle="Identical project keys"
          icon={Copy}
          accent="blue"
          status="healthy"
        />
        <KpiStatCard
          title="Overlapping Staffing"
          value="3 Clashes"
          subtitle="Simultaneous time intervals"
          icon={Layers}
          accent="rose"
          status="warning"
        />
      </div>

      {/* Issues Table */}
      <DataTable
        columns={columns}
        data={issues}
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
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={issueType}
              onChange={(e) => {
                setIssueType(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Anomaly Types</option>
              <option value="OVERALLOCATION">OVERALLOCATION</option>
              <option value="STALE_SKILL">STALE_SKILL</option>
              <option value="DUPLICATE_DEMAND">DUPLICATE_DEMAND</option>
              <option value="OVERLAPPING_ALLOCATION">OVERLAPPING_ALLOCATION</option>
            </select>

            <select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>

            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>
        }
      />

      {/* Resolution Modal */}
      <Modal
        isOpen={isResolveModalOpen}
        onClose={() => setIsResolveModalOpen(false)}
        title="Update Anomaly Resolution"
        description="Change operational state and record audit resolution."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsResolveModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpdateStatus}
              isLoading={isSubmitting}
            >
              Update State
            </Button>
          </>
        }
      >
        {selectedIssue && (
          <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs space-y-1">
              <div className="font-bold text-slate-900">{selectedIssue.title}</div>
              <p className="text-slate-600">{selectedIssue.description}</p>
            </div>

            <Select
              label="Operational Status"
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
            >
              <option value="OPEN">OPEN</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
            </Select>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default ExceptionMonitoringPage;
