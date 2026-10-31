import React, { useState, useEffect, useCallback } from 'react';
import {
  Layers,
  Plus,
  RefreshCw,
  Calendar,
  Clock,
  User,
  FolderGit2,
} from 'lucide-react';
import { planningApi } from '../api/planning';
import { workforceApi } from '../api/workforce';
import { useAuth } from '../context/AuthContext';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function AllocationsPage() {
  const [allocations, setAllocations] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [employeesList, setEmployeesList] = useState([]);
  const [projectsList, setProjectsList] = useState([]);

  const [formData, setFormData] = useState({
    employee_id: '',
    project_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    allocation_percentage: 100,
    allocated_hours_per_week: 40,
    status: 'CONFIRMED',
  });

  const { hasRole } = useAuth();
  const canAllocate = hasRole('ADMIN', 'PROJECT_MANAGER', 'OPERATIONS_PARTNER');

  const fetchAllocations = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await planningApi.listAllocations({
        page,
        page_size: pageSize,
        status,
      });
      setAllocations(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load allocations:', err);
      setAllocations([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, status]);

  useEffect(() => {
    fetchAllocations();
  }, [fetchAllocations]);

  const openCreateModal = async () => {
    setIsModalOpen(true);
    try {
      const [empRes, prjRes] = await Promise.allSettled([
        workforceApi.listEmployees({ page_size: 50 }),
        planningApi.listProjects({ page_size: 50, status: 'ACTIVE' }),
      ]);
      if (empRes.status === 'fulfilled') setEmployeesList(empRes.value?.items || []);
      if (prjRes.status === 'fulfilled') setProjectsList(prjRes.value?.items || []);
    } catch (err) {
      console.error('Failed to load employee/project lists:', err);
    }
  };

  const handleCreateAllocation = async (e) => {
    e.preventDefault();
    if (!formData.employee_id || !formData.project_id) {
      alert('Please select both an employee and a target project');
      return;
    }
    setIsSubmitting(true);
    try {
      await planningApi.createAllocation({
        ...formData,
        allocation_percentage: Number(formData.allocation_percentage),
        allocated_hours_per_week: Number(formData.allocated_hours_per_week),
      });
      setIsModalOpen(false);
      fetchAllocations();
    } catch (err) {
      alert(`Error creating allocation: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'employee',
      header: 'Staff Member',
      cell: (row) => (
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold font-mono text-xs">
            {row.employee?.first_name?.[0] || 'E'}
            {row.employee?.last_name?.[0] || 'M'}
          </div>
          <div>
            <div className="font-semibold text-slate-900">
              {row.employee ? `${row.employee.first_name} ${row.employee.last_name}` : row.employee_id}
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              {row.employee?.business_id || row.business_id}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'project',
      header: 'Assigned Project',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 text-slate-400" />
          <span className="font-medium text-slate-800">
            {row.project?.name || `Project: ${row.project_id}`}
          </span>
        </div>
      ),
    },
    {
      key: 'allocation_percentage',
      header: 'Allocation %',
      align: 'center',
      cell: (row) => (
        <span
          className={`font-mono font-bold text-xs ${
            row.allocation_percentage > 100
              ? 'text-rose-600'
              : row.allocation_percentage === 100
              ? 'text-blue-600'
              : 'text-slate-700'
          }`}
        >
          {row.allocation_percentage}%
        </span>
      ),
    },
    {
      key: 'allocated_hours_per_week',
      header: 'Hours / Week',
      align: 'center',
      cell: (row) => (
        <span className="font-mono text-slate-700 font-medium">
          {row.allocated_hours_per_week}h/wk
        </span>
      ),
    },
    {
      key: 'dates',
      header: 'Staffing Duration',
      cell: (row) => (
        <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
          <Calendar className="h-3 w-3 text-slate-400" />
          <span>{row.start_date} → {row.end_date}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      cell: (row) => (
        <Badge
          variant={
            row.status === 'ACTIVE'
              ? 'success'
              : row.status === 'CONFIRMED'
              ? 'primary'
              : row.status === 'PROPOSED'
              ? 'warning'
              : 'default'
          }
        >
          {row.status}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Resource Allocations
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Master registry of employee project assignments, weekly hours commitments, and delivery schedules.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAllocations}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          {canAllocate && (
            <Button
              variant="primary"
              size="sm"
              icon={Plus}
              onClick={openCreateModal}
            >
              New Allocation
            </Button>
          )}
        </div>
      </div>

      <DataTable
        columns={columns}
        data={allocations}
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
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Allocation Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="PROPOSED">PROPOSED</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        }
      />

      {/* New Allocation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Assign Employee to Project"
        description="Configure staffing duration and weekly contracted hours."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateAllocation}
              isLoading={isSubmitting}
            >
              Save Allocation
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateAllocation} className="space-y-3">
          <Select
            label="Staff Member"
            required
            value={formData.employee_id}
            onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
          >
            <option value="">-- Select Employee --</option>
            {employeesList.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.first_name} {emp.last_name} ({emp.department} • {emp.standard_hours_per_week}h/wk)
              </option>
            ))}
          </Select>

          <Select
            label="Target Project"
            required
            value={formData.project_id}
            onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
          >
            <option value="">-- Select Project --</option>
            {projectsList.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.code})
              </option>
            ))}
          </Select>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date"
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
            <Input
              label="End Date"
              type="date"
              required
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Allocation %"
              type="number"
              min="10"
              max="150"
              value={formData.allocation_percentage}
              onChange={(e) => {
                const pct = Number(e.target.value);
                setFormData({
                  ...formData,
                  allocation_percentage: pct,
                  allocated_hours_per_week: Math.round((pct / 100) * 40),
                });
              }}
            />
            <Input
              label="Hours / Week"
              type="number"
              min="4"
              max="60"
              value={formData.allocated_hours_per_week}
              onChange={(e) => setFormData({ ...formData, allocated_hours_per_week: e.target.value })}
            />
          </div>

          <Select
            label="Status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          >
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="PROPOSED">PROPOSED</option>
            <option value="ACTIVE">ACTIVE</option>
          </Select>
        </form>
      </Modal>
    </div>
  );
}

export default AllocationsPage;
