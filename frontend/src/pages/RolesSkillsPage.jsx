import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Award,
  Plus,
  RefreshCw,
  Search,
  Layers,
  Filter,
} from 'lucide-react';
import { workforceApi } from '../api/workforce';
import { useAuth } from '../context/AuthContext';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Tabs from '../components/ui/Tabs';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function RolesSkillsPage() {
  const [activeTab, setActiveTab] = useState('skills');

  // Skills State
  const [skills, setSkills] = useState([]);
  const [skillsTotal, setSkillsTotal] = useState(0);
  const [skillsPage, setSkillsPage] = useState(1);
  const [skillsPageSize, setSkillsPageSize] = useState(20);
  const [skillsSearch, setSkillsSearch] = useState('');
  const [skillsCategory, setSkillsCategory] = useState('');
  const [isSkillsLoading, setIsSkillsLoading] = useState(true);

  // Roles State
  const [roles, setRoles] = useState([]);
  const [rolesTotal, setRolesTotal] = useState(0);
  const [rolesPage, setRolesPage] = useState(1);
  const [rolesPageSize, setRolesPageSize] = useState(20);
  const [rolesSearch, setRolesSearch] = useState('');
  const [rolesDepartment, setRolesDepartment] = useState('');
  const [isRolesLoading, setIsRolesLoading] = useState(true);

  // Modals
  const [isAddSkillOpen, setIsAddSkillOpen] = useState(false);
  const [isAddRoleOpen, setIsAddRoleOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Skill Form
  const [skillForm, setSkillForm] = useState({
    name: '',
    category: 'BACKEND',
    description: '',
  });

  // Role Form
  const [roleForm, setRoleForm] = useState({
    name: '',
    department: 'Engineering',
    level: 3,
    description: '',
  });

  const { hasRole } = useAuth();
  const canManage = hasRole('ADMIN', 'HR_PARTNER');

  const fetchSkills = useCallback(async () => {
    setIsSkillsLoading(true);
    try {
      const res = await workforceApi.listSkills({
        page: skillsPage,
        page_size: skillsPageSize,
        search: skillsSearch,
        category: skillsCategory,
      });
      setSkills(res.items || []);
      setSkillsTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to fetch skills:', err);
      setSkills([]);
    } finally {
      setIsSkillsLoading(false);
    }
  }, [skillsPage, skillsPageSize, skillsSearch, skillsCategory]);

  const fetchRoles = useCallback(async () => {
    setIsRolesLoading(true);
    try {
      const res = await workforceApi.listRoles({
        page: rolesPage,
        page_size: rolesPageSize,
        search: rolesSearch,
        department: rolesDepartment,
      });
      setRoles(res.items || []);
      setRolesTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
      setRoles([]);
    } finally {
      setIsRolesLoading(false);
    }
  }, [rolesPage, rolesPageSize, rolesSearch, rolesDepartment]);

  useEffect(() => {
    if (activeTab === 'skills') {
      fetchSkills();
    } else {
      fetchRoles();
    }
  }, [activeTab, fetchSkills, fetchRoles]);

  const handleCreateSkill = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await workforceApi.createSkill(skillForm);
      setIsAddSkillOpen(false);
      setSkillForm({ name: '', category: 'BACKEND', description: '' });
      fetchSkills();
    } catch (err) {
      alert(`Error creating skill: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await workforceApi.createRole({
        ...roleForm,
        level: Number(roleForm.level),
      });
      setIsAddRoleOpen(false);
      setRoleForm({ name: '', department: 'Engineering', level: 3, description: '' });
      fetchRoles();
    } catch (err) {
      alert(`Error creating role: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const skillColumns = [
    {
      key: 'name',
      header: 'Skill Name & Identifier',
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-teal-50 text-teal-700 font-bold text-xs border border-teal-100">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900">{row.name}</div>
            <div className="text-[10px] font-mono text-slate-400">{row.business_id}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Taxonomy Category',
      sortable: true,
      cell: (row) => (
        <Badge
          variant={
            row.category === 'AI_ML'
              ? 'purple'
              : row.category === 'CLOUD'
              ? 'primary'
              : row.category === 'BACKEND'
              ? 'teal'
              : 'default'
          }
        >
          {row.category}
        </Badge>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      cell: (row) => (
        <span className="text-slate-500 line-clamp-1 max-w-md">
          {row.description || 'No description provided.'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      cell: (row) => (
        <Badge variant={row.is_active ? 'success' : 'default'} size="sm">
          {row.is_active ? 'ACTIVE' : 'INACTIVE'}
        </Badge>
      ),
    },
  ];

  const roleColumns = [
    {
      key: 'name',
      header: 'Role Title & Identifier',
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-50 text-blue-700 font-bold text-xs border border-blue-100">
            <Briefcase className="h-4 w-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900">{row.name}</div>
            <div className="text-[10px] font-mono text-slate-400">{row.business_id}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'department',
      header: 'Department',
      sortable: true,
      cell: (row) => <span className="font-medium text-slate-800">{row.department}</span>,
    },
    {
      key: 'level',
      header: 'Seniority Level',
      align: 'center',
      cell: (row) => (
        <Badge variant="navy" size="sm">
          Level {row.level}
        </Badge>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      cell: (row) => (
        <span className="text-slate-500 line-clamp-1 max-w-md">
          {row.description || 'Enterprise role specification.'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      cell: (row) => (
        <Badge variant={row.is_active ? 'success' : 'default'} size="sm">
          {row.is_active ? 'ACTIVE' : 'DEPRECATED'}
        </Badge>
      ),
    },
  ];

  const taxonomyTabs = [
    { id: 'skills', label: 'Skill Taxonomy', icon: Award, badge: skillsTotal },
    { id: 'roles', label: 'Job Role Taxonomy', icon: Briefcase, badge: rolesTotal },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Roles & Skills Taxonomy
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Standardized corporate competency frameworks, seniority levels, and domain classifications.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canManage && (
            <Button
              variant="primary"
              size="sm"
              icon={Plus}
              onClick={() => {
                if (activeTab === 'skills') setIsAddSkillOpen(true);
                else setIsAddRoleOpen(true);
              }}
            >
              {activeTab === 'skills' ? 'Add Skill' : 'Add Role'}
            </Button>
          )}
        </div>
      </div>

      <Tabs tabs={taxonomyTabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'skills' ? (
        <DataTable
          columns={skillColumns}
          data={skills}
          total={skillsTotal}
          page={skillsPage}
          pageSize={skillsPageSize}
          totalPages={Math.max(1, Math.ceil(skillsTotal / skillsPageSize))}
          isLoading={isSkillsLoading}
          onPageChange={setSkillsPage}
          onPageSizeChange={(sz) => {
            setSkillsPageSize(sz);
            setSkillsPage(1);
          }}
          searchQuery={skillsSearch}
          onSearchChange={(q) => {
            setSkillsSearch(q);
            setSkillsPage(1);
          }}
          searchPlaceholder="Search skill taxonomy (e.g. 'Kubernetes', 'Python')..."
          filterComponent={
            <select
              value={skillsCategory}
              onChange={(e) => {
                setSkillsCategory(e.target.value);
                setSkillsPage(1);
              }}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="">All Categories</option>
              <option value="BACKEND">BACKEND</option>
              <option value="FRONTEND">FRONTEND</option>
              <option value="CLOUD">CLOUD</option>
              <option value="DATA">DATA</option>
              <option value="AI_ML">AI_ML</option>
              <option value="DEVOPS">DEVOPS</option>
              <option value="SECURITY">SECURITY</option>
              <option value="MANAGEMENT">MANAGEMENT</option>
            </select>
          }
        />
      ) : (
        <DataTable
          columns={roleColumns}
          data={roles}
          total={rolesTotal}
          page={rolesPage}
          pageSize={rolesPageSize}
          totalPages={Math.max(1, Math.ceil(rolesTotal / rolesPageSize))}
          isLoading={isRolesLoading}
          onPageChange={setRolesPage}
          onPageSizeChange={(sz) => {
            setRolesPageSize(sz);
            setRolesPage(1);
          }}
          searchQuery={rolesSearch}
          onSearchChange={(q) => {
            setRolesSearch(q);
            setRolesPage(1);
          }}
          searchPlaceholder="Search role titles..."
          filterComponent={
            <select
              value={rolesDepartment}
              onChange={(e) => {
                setRolesDepartment(e.target.value);
                setRolesPage(1);
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
            </select>
          }
        />
      )}

      {/* Add Skill Modal */}
      <Modal
        isOpen={isAddSkillOpen}
        onClose={() => setIsAddSkillOpen(false)}
        title="Register New Skill"
        description="Add a competency to the enterprise taxonomy."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsAddSkillOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateSkill}
              isLoading={isSubmitting}
            >
              Create Skill
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSkill} className="space-y-3">
          <Input
            label="Skill Name"
            required
            value={skillForm.name}
            onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
            placeholder="e.g. PyTorch, Rust, AWS EKS"
          />
          <Select
            label="Category"
            value={skillForm.category}
            onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })}
          >
            <option value="BACKEND">BACKEND</option>
            <option value="FRONTEND">FRONTEND</option>
            <option value="CLOUD">CLOUD</option>
            <option value="DATA">DATA</option>
            <option value="AI_ML">AI_ML</option>
            <option value="DEVOPS">DEVOPS</option>
            <option value="SECURITY">SECURITY</option>
            <option value="MANAGEMENT">MANAGEMENT</option>
          </Select>
          <Input
            label="Description"
            value={skillForm.description}
            onChange={(e) => setSkillForm({ ...skillForm, description: e.target.value })}
            placeholder="Technical scope and enterprise applicability"
          />
        </form>
      </Modal>

      {/* Add Role Modal */}
      <Modal
        isOpen={isAddRoleOpen}
        onClose={() => setIsAddRoleOpen(false)}
        title="Register Job Role"
        description="Add a job family position to the corporate catalog."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsAddRoleOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateRole}
              isLoading={isSubmitting}
            >
              Create Role
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateRole} className="space-y-3">
          <Input
            label="Role Title"
            required
            value={roleForm.name}
            onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
            placeholder="e.g. Staff Distributed Systems Engineer"
          />
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Department"
              value={roleForm.department}
              onChange={(e) => setRoleForm({ ...roleForm, department: e.target.value })}
            >
              <option value="Engineering">Engineering</option>
              <option value="Data & Analytics">Data & Analytics</option>
              <option value="Cloud Architecture">Cloud Architecture</option>
              <option value="Product">Product</option>
              <option value="Design">Design</option>
              <option value="Consulting">Consulting</option>
            </Select>

            <Select
              label="Seniority Level (1-10)"
              value={roleForm.level}
              onChange={(e) => setRoleForm({ ...roleForm, level: e.target.value })}
            >
              <option value="1">Level 1 - Associate / Junior</option>
              <option value="2">Level 2 - Mid-Level Specialist</option>
              <option value="3">Level 3 - Senior Specialist</option>
              <option value="4">Level 4 - Staff / Lead</option>
              <option value="5">Level 5 - Principal / Architect</option>
              <option value="6">Level 6 - Director / VP</option>
            </Select>
          </div>
          <Input
            label="Role Description"
            value={roleForm.description}
            onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
            placeholder="Key accountabilities and skill expectations"
          />
        </form>
      </Modal>
    </div>
  );
}

export default RolesSkillsPage;
