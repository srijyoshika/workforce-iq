import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  UserPlus,
  RefreshCw,
  ExternalLink,
  Mail,
  MapPin,
  Calendar,
  Building,
  Briefcase,
  Award,
  Sparkles,
} from 'lucide-react';
import { workforceApi } from '../api/workforce';
import { useAuth } from '../context/AuthContext';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [status, setStatus] = useState('');
  const [sortBy, setSortBy] = useState('last_name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [isLoading, setIsLoading] = useState(true);

  // Add Employee Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [rolesList, setRolesList] = useState([]);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    department: 'Engineering',
    location: 'New York, NY',
    employment_status: 'ACTIVE',
    hire_date: new Date().toISOString().split('T')[0],
    standard_hours_per_week: 40,
    system_role: 'EMPLOYEE',
    role_id: '',
    years_of_experience: 4,
    experience_level: 'Mid-Level',
    previous_company: '',
    experience_summary: '',
  });
  const [formError, setFormError] = useState(null);

  const { hasRole } = useAuth();
  const canAddEmployee = hasRole('ADMIN', 'HR_PARTNER');
  const navigate = useNavigate();

  // Load organizational roles for role assignment
  useEffect(() => {
    workforceApi.listRoles({ page_size: 100 })
      .then((res) => setRolesList(res.items || res || []))
      .catch((err) => console.error('Failed to load roles for registration modal:', err));
  }, []);

  const fetchEmployees = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await workforceApi.listEmployees({
        page,
        page_size: pageSize,
        search,
        department,
        status,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setEmployees(res.items || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      console.error('Failed to fetch employees:', err);
      setEmployees([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, search, department, status, sortBy, sortOrder]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      await workforceApi.createEmployee({
        ...formData,
        role_id: formData.role_id || null,
        years_of_experience: Number(formData.years_of_experience) || 0,
        standard_hours_per_week: Number(formData.standard_hours_per_week),
      });
      setIsAddModalOpen(false);
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        department: 'Engineering',
        location: 'New York, NY',
        employment_status: 'ACTIVE',
        hire_date: new Date().toISOString().split('T')[0],
        standard_hours_per_week: 40,
        system_role: 'EMPLOYEE',
        role_id: '',
        years_of_experience: 4,
        experience_level: 'Mid-Level',
        previous_company: '',
        experience_summary: '',
      });
      fetchEmployees();
    } catch (err) {
      setFormError(err.message || 'Failed to register employee record');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Employee Details',
      sortable: true,
      sortKey: 'last_name',
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-700 font-bold font-mono text-xs border border-blue-100 shrink-0">
            {row.first_name[0]}
            {row.last_name[0]}
          </div>
          <div>
            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
              <span>{row.first_name} {row.last_name}</span>
              <span className="font-mono text-[10px] text-slate-400 font-normal">({row.business_id})</span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
              <Mail className="h-3 w-3 text-slate-400" />
              <span>{row.email}</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'department',
      header: 'Department & Location',
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-medium text-slate-800 flex items-center gap-1">
            <Building className="h-3 w-3 text-slate-400" />
            <span>{row.department}</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <MapPin className="h-3 w-3 text-slate-300" />
            <span>{row.location}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'experience',
      header: 'Experience',
      cell: (row) => (
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-slate-800 flex items-center gap-1">
            <Briefcase className="h-3 w-3 text-blue-500" />
            {row.years_of_experience ? `${row.years_of_experience} yrs` : (row.experience_level || 'Mid-Level')}
          </span>
          <span className="text-[10px] text-slate-400">
            {row.experience_level || 'General'}
          </span>
        </div>
      ),
    },
    {
      key: 'employment_status',
      header: 'Status',
      sortable: true,
      cell: (row) => (
        <Badge
          variant={
            row.employment_status === 'ACTIVE'
              ? 'success'
              : row.employment_status === 'ON_LEAVE'
              ? 'warning'
              : 'default'
          }
        >
          {row.employment_status}
        </Badge>
      ),
    },
    {
      key: 'standard_hours_per_week',
      header: 'Weekly Contract',
      align: 'center',
      cell: (row) => (
        <span className="font-mono font-medium text-slate-700">
          {row.standard_hours_per_week}h/wk
        </span>
      ),
    },
    {
      key: 'system_role',
      header: 'Role Access',
      cell: (row) => (
        <Badge variant="navy" size="sm">
          {row.system_role || 'EMPLOYEE'}
        </Badge>
      ),
    },
    {
      key: 'hire_date',
      header: 'Hire Date',
      sortable: true,
      cell: (row) => (
        <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
          <Calendar className="h-3 w-3 text-slate-400" />
          <span>{row.hire_date}</span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      cell: (row) => (
        <Button
          size="sm"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/employees/${row.id}`);
          }}
          icon={ExternalLink}
          className="h-8 px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        >
          Profile
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Employee Directory
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Comprehensive registry of enterprise personnel, contractual capacity, and system roles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchEmployees}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh
          </Button>
          {canAddEmployee && (
            <Button
              variant="primary"
              size="sm"
              icon={UserPlus}
              onClick={() => setIsAddModalOpen(true)}
            >
              Add Employee
            </Button>
          )}
        </div>
      </div>

      {/* Server-side Filter Bar */}
      <DataTable
        columns={columns}
        data={employees}
        total={total}
        page={page}
        pageSize={pageSize}
        totalPages={totalPages}
        isLoading={isLoading}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={(key, order) => {
          setSortBy(key);
          setSortOrder(order);
          setPage(1);
        }}
        onPageChange={(p) => setPage(p)}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setPage(1);
        }}
        searchQuery={search}
        onSearchChange={(q) => {
          setSearch(q);
          setPage(1);
        }}
        searchPlaceholder="Search by name, email, or employee ID..."
        filterComponent={
          <div className="flex items-center gap-2">
            <select
              value={department}
              onChange={(e) => {
                setDepartment(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Departments</option>
              <option value="Engineering">Engineering</option>
              <option value="Data & Analytics">Data & Analytics</option>
              <option value="Cloud Architecture">Cloud Architecture</option>
              <option value="Product">Product</option>
              <option value="Design">Design</option>
              <option value="Consulting">Consulting</option>
              <option value="Executive">Executive</option>
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
              <option value="ACTIVE">ACTIVE</option>
              <option value="ON_LEAVE">ON_LEAVE</option>
              <option value="TERMINATED">TERMINATED</option>
              <option value="PROBATION">PROBATION</option>
            </select>
          </div>
        }
        onRowClick={(row) => navigate(`/employees/${row.id}`)}
      />

      {/* Add Employee Dialog Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Register New Employee"
        description="Enter contract parameters, professional experience, and corporate profile."
        maxWidth="max-w-2xl"
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateEmployee}
              isLoading={isSubmitting}
            >
              Save Employee
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateEmployee} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name"
              required
              placeholder="e.g. Sarah"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            />
            <Input
              label="Last Name"
              required
              placeholder="e.g. Jenkins"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            />
          </div>

          <Input
            label="Corporate Email"
            type="email"
            required
            placeholder="e.g. s.jenkins@company.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            >
              <option value="Engineering">Engineering</option>
              <option value="Data & Analytics">Data & Analytics</option>
              <option value="Cloud Architecture">Cloud Architecture</option>
              <option value="Product">Product</option>
              <option value="Design">Design</option>
              <option value="Consulting">Consulting</option>
              <option value="Operations">Operations</option>
            </Select>

            <Input
              label="Location"
              required
              placeholder="e.g. New York, NY"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Hire Date"
              type="date"
              required
              value={formData.hire_date}
              onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
            />
            <Input
              label="Weekly Hours"
              type="number"
              min="10"
              max="60"
              value={formData.standard_hours_per_week}
              onChange={(e) => setFormData({ ...formData, standard_hours_per_week: e.target.value })}
            />
          </div>

          <Select
            label="System Access Role"
            value={formData.system_role}
            onChange={(e) => setFormData({ ...formData, system_role: e.target.value })}
          >
            <option value="EMPLOYEE">EMPLOYEE</option>
            <option value="PROJECT_MANAGER">PROJECT_MANAGER</option>
            <option value="OPERATIONS_PARTNER">OPERATIONS_PARTNER</option>
            <option value="HR_PARTNER">HR_PARTNER</option>
            <option value="ADMIN">ADMIN</option>
          </Select>

          {/* Professional Experience & Seniority Block */}
          <div className="rounded-xl border border-slate-200/90 bg-slate-50/70 p-4 space-y-3.5">
            <div className="flex items-center justify-between border-b border-slate-200/80 pb-2.5">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-semibold shadow-xs">
                  <Briefcase className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Professional Experience & Seniority
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    Prior industry tenure, competency classification and organizational role
                  </p>
                </div>
              </div>
              <Badge variant="teal" size="sm">
                {formData.years_of_experience || 0} Years Exp
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Years of Experience"
                type="number"
                step="0.5"
                min="0"
                max="50"
                placeholder="e.g. 5"
                value={formData.years_of_experience}
                onChange={(e) => {
                  const val = parseFloat(e.target.value) || 0;
                  let autoLevel = 'Mid-Level';
                  if (val < 2) autoLevel = 'Junior';
                  else if (val <= 5) autoLevel = 'Mid-Level';
                  else if (val <= 8) autoLevel = 'Senior';
                  else if (val <= 12) autoLevel = 'Lead / Staff';
                  else autoLevel = 'Principal / Executive';

                  setFormData({
                    ...formData,
                    years_of_experience: e.target.value,
                    experience_level: autoLevel,
                  });
                }}
              />

              <Select
                label="Seniority / Experience Level"
                value={formData.experience_level}
                onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
              >
                <option value="Junior">Junior (0 - 2 yrs)</option>
                <option value="Mid-Level">Mid-Level (3 - 5 yrs)</option>
                <option value="Senior">Senior (5 - 8 yrs)</option>
                <option value="Lead / Staff">Lead / Staff (8 - 12 yrs)</option>
                <option value="Principal / Executive">Principal / Executive (12+ yrs)</option>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Select
                label="Assigned Primary Role"
                value={formData.role_id}
                onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
              >
                <option value="">-- Choose Role from Taxonomy --</option>
                {rolesList.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title || r.name} ({r.department})
                  </option>
                ))}
              </Select>

              <Input
                label="Previous Employer / Company"
                placeholder="e.g. Google, Stripe, Microsoft"
                value={formData.previous_company}
                onChange={(e) => setFormData({ ...formData, previous_company: e.target.value })}
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Experience Summary & Core Competencies
              </label>
              <textarea
                rows="2"
                className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 transition-colors"
                placeholder="e.g. 5+ years specializing in distributed systems, Kubernetes orchestration, Python backend services, and high-throughput real-time pipelines."
                value={formData.experience_summary}
                onChange={(e) => setFormData({ ...formData, experience_summary: e.target.value })}
              />
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default EmployeesPage;
