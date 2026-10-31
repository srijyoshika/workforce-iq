import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Plus,
  RefreshCw,
  Clock,
  User,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { workforceApi } from '../api/workforce';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function AvailabilityPage() {
  const [availabilityList, setAvailabilityList] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [availabilityType, setAvailabilityType] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Leave Request Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [employeesList, setEmployeesList] = useState([]);

  const [formData, setFormData] = useState({
    employee_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    availability_type: 'PTO',
    capacity_percentage: 0,
    available_hours_per_day: 0,
    reason: 'Annual Paid Time Off',
    is_approved: true,
  });

  const fetchAvailability = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await workforceApi.listAvailability({
        page,
        page_size: pageSize,
        availability_type: availabilityType,
      });
      setAvailabilityList(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load availability:', err);
      setAvailabilityList([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, availabilityType]);

  useEffect(() => {
    fetchAvailability();
  }, [fetchAvailability]);

  const openCreateModal = async () => {
    setIsModalOpen(true);
    try {
      const empRes = await workforceApi.listEmployees({ page_size: 50 });
      setEmployeesList(empRes.items || []);
    } catch (err) {
      console.error('Failed to load employees:', err);
    }
  };

  const handleCreateLeave = async (e) => {
    e.preventDefault();
    if (!formData.employee_id) {
      alert('Please select an employee');
      return;
    }
    setIsSubmitting(true);
    try {
      await workforceApi.createAvailability({
        ...formData,
        capacity_percentage: Number(formData.capacity_percentage),
        available_hours_per_day: Number(formData.available_hours_per_day),
      });
      setIsModalOpen(false);
      fetchAvailability();
    } catch (err) {
      alert(`Error submitting leave: ${err.message}`);
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
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-100 text-teal-800 font-bold font-mono text-xs">
            {row.employee?.first_name?.[0] || 'E'}
            {row.employee?.last_name?.[0] || 'M'}
          </div>
          <div>
            <div className="font-semibold text-slate-900">
              {row.employee ? `${row.employee.first_name} ${row.employee.last_name}` : row.employee_id}
            </div>
            <div className="text-[10px] font-mono text-slate-400">{row.business_id}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'availability_type',
      header: 'Absence / Leave Type',
      cell: (row) => (
        <Badge
          variant={
            row.availability_type === 'PTO'
              ? 'primary'
              : row.availability_type === 'SICK_LEAVE'
              ? 'warning'
              : row.availability_type === 'TRAINING'
              ? 'teal'
              : 'default'
          }
        >
          {row.availability_type}
        </Badge>
      ),
    },
    {
      key: 'dates',
      header: 'Period Dates',
      cell: (row) => (
        <div className="text-[11px] text-slate-600 font-mono flex items-center gap-1">
          <Calendar className="h-3 w-3 text-slate-400" />
          <span>{row.start_date} → {row.end_date}</span>
        </div>
      ),
    },
    {
      key: 'capacity_percentage',
      header: 'Effective Capacity',
      align: 'center',
      cell: (row) => (
        <span className="font-mono text-xs text-slate-700">
          {row.capacity_percentage}%
        </span>
      ),
    },
    {
      key: 'reason',
      header: 'Reason / Notes',
      cell: (row) => (
        <span className="text-slate-500 line-clamp-1 max-w-sm">
          {row.reason || 'Standard scheduled leave'}
        </span>
      ),
    },
    {
      key: 'is_approved',
      header: 'Approval',
      cell: (row) => (
        <Badge variant={row.is_approved ? 'success' : 'warning'} size="sm">
          {row.is_approved ? 'APPROVED' : 'PENDING'}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Availability & Leave Management
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Workforce capacity calendar, scheduled PTO, holidays, and training leave deductions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAvailability}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={openCreateModal}
          >
            Record Leave
          </Button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={availabilityList}
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
            value={availabilityType}
            onChange={(e) => {
              setAvailabilityType(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
          >
            <option value="">All Leave Types</option>
            <option value="PTO">PTO</option>
            <option value="SICK_LEAVE">SICK_LEAVE</option>
            <option value="HOLIDAY">HOLIDAY</option>
            <option value="TRAINING">TRAINING</option>
            <option value="BENCH">BENCH</option>
          </select>
        }
      />

      {/* Record Leave Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Schedule Leave / Absence Period"
        description="Records an availability deduction for capacity and utilization calculations."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateLeave}
              isLoading={isSubmitting}
            >
              Confirm Leave Record
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateLeave} className="space-y-3">
          <Select
            label="Staff Member"
            required
            value={formData.employee_id}
            onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
          >
            <option value="">-- Choose Employee --</option>
            {employeesList.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.first_name} {emp.last_name} ({emp.department})
              </option>
            ))}
          </Select>

          <Select
            label="Absence Type"
            value={formData.availability_type}
            onChange={(e) => setFormData({ ...formData, availability_type: e.target.value })}
          >
            <option value="PTO">PTO (Paid Time Off)</option>
            <option value="SICK_LEAVE">SICK_LEAVE (Medical)</option>
            <option value="HOLIDAY">HOLIDAY (Official Public)</option>
            <option value="TRAINING">TRAINING (Upskilling)</option>
            <option value="BENCH">BENCH (Between Engagements)</option>
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

          <Input
            label="Reason / Manager Notes"
            value={formData.reason}
            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
          />
        </form>
      </Modal>
    </div>
  );
}

export default AvailabilityPage;
