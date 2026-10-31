import React, { useState, useEffect, useCallback } from 'react';
import {
  GraduationCap,
  Plus,
  RefreshCw,
  Award,
  Calendar,
  DollarSign,
  Clock,
} from 'lucide-react';
import { workforceApi } from '../api/workforce';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function TrainingPage() {
  const [trainingList, setTrainingList] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Enroll Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [employeesList, setEmployeesList] = useState([]);
  const [skillsList, setSkillsList] = useState([]);

  const [formData, setFormData] = useState({
    employee_id: '',
    skill_id: '',
    program_name: 'Advanced Distributed Systems Mastery',
    provider: 'WorkforceIQ Academy',
    start_date: new Date().toISOString().split('T')[0],
    target_completion_date: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    target_proficiency: 4,
    cost: 1500,
    hours_per_week: 8,
    status: 'ENROLLED',
  });

  const fetchTraining = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await workforceApi.listTraining({
        page,
        page_size: pageSize,
        status,
      });
      setTrainingList(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load training:', err);
      setTrainingList([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, status]);

  useEffect(() => {
    fetchTraining();
  }, [fetchTraining]);

  const openEnrollModal = async () => {
    setIsModalOpen(true);
    try {
      const [empRes, sklRes] = await Promise.allSettled([
        workforceApi.listEmployees({ page_size: 50 }),
        workforceApi.listSkills({ page_size: 100 }),
      ]);
      if (empRes.status === 'fulfilled') setEmployeesList(empRes.value?.items || []);
      if (sklRes.status === 'fulfilled') setSkillsList(sklRes.value?.items || []);
    } catch (err) {
      console.error('Failed to load employee/skill taxonomy:', err);
    }
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!formData.employee_id || !formData.skill_id) {
      alert('Please select both an employee and a target competency');
      return;
    }
    setIsSubmitting(true);
    try {
      await workforceApi.createTraining({
        ...formData,
        target_proficiency: Number(formData.target_proficiency),
        cost: Number(formData.cost),
        hours_per_week: Number(formData.hours_per_week),
      });
      setIsModalOpen(false);
      fetchTraining();
    } catch (err) {
      alert(`Error enrolling in training: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'employee',
      header: 'Enrolled Employee',
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
            <div className="text-[10px] font-mono text-slate-400">{row.business_id}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'program',
      header: 'Training Track & Provider',
      cell: (row) => (
        <div>
          <div className="font-semibold text-slate-900">{row.program_name}</div>
          <div className="text-[10px] text-slate-500">{row.provider || 'Internal Academy'}</div>
        </div>
      ),
    },
    {
      key: 'target_proficiency',
      header: 'Target Proficiency',
      align: 'center',
      cell: (row) => (
        <Badge variant="navy" size="sm">
          Level {row.target_proficiency}/5
        </Badge>
      ),
    },
    {
      key: 'commitment',
      header: 'Hours & Cost',
      cell: (row) => (
        <div className="text-xs font-mono text-slate-700">
          <span>{row.hours_per_week}h/wk</span>
          <span className="text-slate-400 mx-1">•</span>
          <span className="text-slate-900 font-semibold">${row.cost}</span>
        </div>
      ),
    },
    {
      key: 'completion',
      header: 'Target Date',
      cell: (row) => (
        <span className="text-[11px] font-mono text-slate-600">
          {row.target_completion_date}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      cell: (row) => (
        <Badge
          variant={
            row.status === 'COMPLETED'
              ? 'success'
              : row.status === 'IN_PROGRESS' || row.status === 'ENROLLED'
              ? 'primary'
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
            Training & Upskilling Management
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Track employee career tracks, certification progress, and internal capability development.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTraining}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={openEnrollModal}
          >
            Enroll in Training
          </Button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={trainingList}
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
            <option value="">All Statuses</option>
            <option value="ENROLLED">ENROLLED</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="PLANNED">PLANNED</option>
          </select>
        }
      />

      {/* Enroll Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Enroll Employee in Upskilling Program"
        description="Assign a structured development track to bridge capability deficits."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleEnroll}
              isLoading={isSubmitting}
            >
              Confirm Enrollment
            </Button>
          </>
        }
      >
        <form onSubmit={handleEnroll} className="space-y-3">
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
            label="Target Competency (Skill)"
            required
            value={formData.skill_id}
            onChange={(e) => setFormData({ ...formData, skill_id: e.target.value })}
          >
            <option value="">-- Choose Target Skill --</option>
            {skillsList.map((skl) => (
              <option key={skl.id} value={skl.id}>
                {skl.name} ({skl.category})
              </option>
            ))}
          </Select>

          <Input
            label="Program Name"
            required
            value={formData.program_name}
            onChange={(e) => setFormData({ ...formData, program_name: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Provider"
              value={formData.provider}
              onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
            />
            <Select
              label="Target Proficiency"
              value={formData.target_proficiency}
              onChange={(e) => setFormData({ ...formData, target_proficiency: e.target.value })}
            >
              <option value="2">Level 2 - Working Knowledge</option>
              <option value="3">Level 3 - Intermediate / Autonomous</option>
              <option value="4">Level 4 - Advanced / SME</option>
              <option value="5">Level 5 - Principal Authority</option>
            </Select>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Weekly Hours"
              type="number"
              min="1"
              max="20"
              value={formData.hours_per_week}
              onChange={(e) => setFormData({ ...formData, hours_per_week: e.target.value })}
            />
            <Input
              label="Budget Cost ($)"
              type="number"
              min="0"
              value={formData.cost}
              onChange={(e) => setFormData({ ...formData, cost: e.target.value })}
            />
            <Input
              label="Target Completion"
              type="date"
              required
              value={formData.target_completion_date}
              onChange={(e) => setFormData({ ...formData, target_completion_date: e.target.value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default TrainingPage;
