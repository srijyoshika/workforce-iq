import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderGit2,
  Plus,
  RefreshCw,
  Calendar,
  DollarSign,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { planningApi } from '../api/planning';
import { useAuth } from '../context/AuthContext';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Create Project Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    status: 'ACTIVE',
    budget: 150000,
    priority: 2,
    description: '',
  });

  const { hasRole } = useAuth();
  const canManageProjects = hasRole('ADMIN', 'PROJECT_MANAGER', 'OPERATIONS_PARTNER');

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await planningApi.listProjects({
        page,
        page_size: pageSize,
        search,
        status,
        priority,
      });
      setProjects(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, search, status, priority]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await planningApi.createProject({
        ...formData,
        budget: Number(formData.budget),
        priority: Number(formData.priority),
      });
      setIsCreateOpen(false);
      setFormData({
        name: '',
        code: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        status: 'ACTIVE',
        budget: 150000,
        priority: 2,
        description: '',
      });
      fetchProjects();
    } catch (err) {
      alert(`Error creating project: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Project Name & Code',
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-900 text-white font-mono text-xs font-bold shrink-0">
            {row.code?.substring(0, 2) || 'PR'}
          </div>
          <div>
            <div className="font-semibold text-slate-900">{row.name}</div>
            <div className="text-[10px] font-mono text-slate-400">
              {row.code} • {row.business_id}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      cell: (row) => (
        <Badge
          variant={
            row.status === 'ACTIVE'
              ? 'success'
              : row.status === 'COMPLETED'
              ? 'teal'
              : row.status === 'PIPELINE'
              ? 'primary'
              : row.status === 'ON_HOLD'
              ? 'warning'
              : 'default'
          }
        >
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'priority',
      header: 'Priority',
      align: 'center',
      cell: (row) => (
        <Badge
          variant={
            row.priority === 1
              ? 'critical'
              : row.priority === 2
              ? 'warning'
              : 'default'
          }
          size="sm"
        >
          P{row.priority}
        </Badge>
      ),
    },
    {
      key: 'dates',
      header: 'Delivery Horizon',
      cell: (row) => (
        <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
          <Calendar className="h-3 w-3 text-slate-400" />
          <span>{row.start_date} → {row.end_date}</span>
        </div>
      ),
    },
    {
      key: 'budget',
      header: 'Allocated Budget',
      align: 'right',
      cell: (row) => (
        <span className="font-mono font-semibold text-slate-800">
          ${Number(row.budget || 0).toLocaleString()}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Project Portfolio Management
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Pipeline initiatives, project schedules, delivery horizons, and staffing demand.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProjects}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          {canManageProjects && (
            <Button
              variant="primary"
              size="sm"
              icon={Plus}
              onClick={() => setIsCreateOpen(true)}
            >
              New Project
            </Button>
          )}
        </div>
      </div>

      <DataTable
        columns={columns}
        data={projects}
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
        searchQuery={search}
        onSearchChange={(q) => {
          setSearch(q);
          setPage(1);
        }}
        searchPlaceholder="Search projects by name, code or ID..."
        filterComponent={
          <div className="flex items-center gap-2">
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="PIPELINE">PIPELINE</option>
              <option value="APPROVED">APPROVED</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="ON_HOLD">ON_HOLD</option>
            </select>

            <select
              value={priority}
              onChange={(e) => {
                setPriority(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Priorities</option>
              <option value="1">Priority 1 (Urgent)</option>
              <option value="2">Priority 2 (High)</option>
              <option value="3">Priority 3 (Medium)</option>
              <option value="4">Priority 4 (Low)</option>
            </select>
          </div>
        }
      />

      {/* New Project Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Client Project"
        description="Initialize a new delivery initiative and configure schedule bounds."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateProject}
              isLoading={isSubmitting}
            >
              Create Project
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateProject} className="space-y-3">
          <Input
            label="Project Name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g. Core Banking Cloud Migration"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Project Code"
              required
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              placeholder="e.g. PRJ-BANK-01"
            />
            <Select
              label="Priority"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            >
              <option value="1">Priority 1 (Critical)</option>
              <option value="2">Priority 2 (High)</option>
              <option value="3">Priority 3 (Medium)</option>
              <option value="4">Priority 4 (Low)</option>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date"
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
            <Input
              label="Target End Date"
              type="date"
              required
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Budget ($ USD)"
              type="number"
              min="0"
              value={formData.budget}
              onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
            />
            <Select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="PIPELINE">PIPELINE</option>
              <option value="APPROVED">APPROVED</option>
              <option value="DRAFT">DRAFT</option>
            </Select>
          </div>

          <Input
            label="Project Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Key deliverables and business goals"
          />
        </form>
      </Modal>
    </div>
  );
}

export default ProjectsPage;
