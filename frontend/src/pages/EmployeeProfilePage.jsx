import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Building,
  MapPin,
  Calendar,
  Clock,
  DollarSign,
  Shield,
  Award,
  Layers,
  GraduationCap,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Briefcase,
  Sparkles,
} from 'lucide-react';
import { workforceApi } from '../api/workforce';
import { planningApi } from '../api/planning';
import { intelligenceApi } from '../api/intelligence';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Tabs from '../components/ui/Tabs';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { CardSkeleton, TableSkeleton } from '../components/ui/Skeleton';

export function EmployeeProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [employee, setEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState('skills');
  const [skills, setSkills] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [training, setTraining] = useState([]);
  const [utilization, setUtilization] = useState(null);
  const [capacity, setCapacity] = useState(null);
  const [allSkillsTaxonomy, setAllSkillsTaxonomy] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add Skill Modal
  const [isAddSkillOpen, setIsAddSkillOpen] = useState(false);
  const [skillForm, setSkillForm] = useState({
    skill_id: '',
    proficiency_level: 3,
    verification_status: 'VERIFIED',
    verified_at: new Date().toISOString().split('T')[0],
  });
  const [isSavingSkill, setIsSavingSkill] = useState(false);

  const fetchProfileData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [
        empData,
        skillsData,
        allocData,
        availData,
        trainData,
        taxonomyRes,
      ] = await Promise.allSettled([
        workforceApi.getEmployee(id),
        workforceApi.getEmployeeSkills(id),
        planningApi.listAllocations({ employee_id: id }),
        workforceApi.listAvailability({ employee_id: id }),
        workforceApi.listTraining({ employee_id: id }),
        workforceApi.listSkills({ page_size: 100 }),
      ]);

      if (empData.status === 'fulfilled') {
        setEmployee(empData.value);
      } else {
        throw new Error(`Employee record with identifier '${id}' not found`);
      }

      setSkills(skillsData.status === 'fulfilled' ? skillsData.value || [] : []);
      setAllocations(allocData.status === 'fulfilled' ? allocData.value?.items || [] : []);
      setAvailability(availData.status === 'fulfilled' ? availData.value?.items || [] : []);
      setTraining(trainData.status === 'fulfilled' ? trainData.value?.items || [] : []);
      setAllSkillsTaxonomy(taxonomyRes.status === 'fulfilled' ? taxonomyRes.value?.items || [] : []);

      // Calculate live utilization & capacity for current period
      const today = new Date().toISOString().split('T')[0];
      const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const [utilRes, capRes] = await Promise.allSettled([
        intelligenceApi.calculateUtilization(id, today, nextMonth),
        intelligenceApi.calculateCapacity(id, today, nextMonth),
      ]);

      if (utilRes.status === 'fulfilled') setUtilization(utilRes.value);
      if (capRes.status === 'fulfilled') setCapacity(capRes.value);
    } catch (err) {
      setError(err.message || 'Error loading employee profile');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProfileData();
  }, [fetchProfileData]);

  const handleAddSkill = async (e) => {
    e.preventDefault();
    if (!skillForm.skill_id) return;
    setIsSavingSkill(true);
    try {
      await workforceApi.addEmployeeSkill({
        employee_id: id,
        skill_id: skillForm.skill_id,
        proficiency_level: Number(skillForm.proficiency_level),
        verification_status: skillForm.verification_status,
        verified_at: skillForm.verified_at,
        is_current: true,
      });
      setIsAddSkillOpen(false);
      const updatedSkills = await workforceApi.getEmployeeSkills(id);
      setSkills(updatedSkills || []);
    } catch (err) {
      alert(`Failed to add skill: ${err.message}`);
    } finally {
      setIsSavingSkill(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <TableSkeleton rows={6} cols={4} />
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center space-y-3">
        <AlertTriangle className="h-8 w-8 text-rose-600 mx-auto" />
        <h3 className="text-base font-bold text-rose-900">Employee Not Found</h3>
        <p className="text-xs text-rose-700">{error || 'The requested profile does not exist.'}</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/employees')}>
          Return to Directory
        </Button>
      </div>
    );
  }

  const profileTabs = [
    { id: 'skills', label: 'Skill Taxonomy', icon: Award, badge: skills.length },
    { id: 'allocations', label: 'Project Allocations', icon: Layers, badge: allocations.length },
    { id: 'availability', label: 'Availability & Leave', icon: Calendar, badge: availability.length },
    { id: 'utilization', label: 'Workload & Capacity', icon: Sliders },
    { id: 'training', label: 'Upskilling & Training', icon: GraduationCap, badge: training.length },
  ];

  return (
    <div className="space-y-6">
      {/* Back button & Action Header */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/employees')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Directory</span>
        </button>
        <div className="flex items-center gap-2">
          <Badge variant="navy">{employee.system_role || 'EMPLOYEE'}</Badge>
          <Badge
            variant={
              employee.employment_status === 'ACTIVE'
                ? 'success'
                : employee.employment_status === 'ON_LEAVE'
                ? 'warning'
                : 'default'
            }
          >
            {employee.employment_status}
          </Badge>
        </div>
      </div>

      {/* Main Profile Header Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-navy-900 text-white font-mono font-bold text-xl shadow-md">
                {employee.first_name[0]}
                {employee.last_name[0]}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-slate-900">
                    {employee.first_name} {employee.last_name}
                  </h1>
                  <span className="font-mono text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                    {employee.business_id}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Mail className="h-3.5 w-3.5 text-slate-400" />
                    {employee.email}
                  </span>
                  <span className="flex items-center gap-1">
                    <Building className="h-3.5 w-3.5 text-slate-400" />
                    {employee.department}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    {employee.location}
                  </span>
                </div>
              </div>
            </div>

            {/* Contract & Seniority Highlights */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 w-full md:w-auto">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Experience
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {employee.years_of_experience != null ? `${employee.years_of_experience} yrs` : '—'}
                </span>
                <span className="text-[10px] font-semibold text-blue-600 block">
                  {employee.experience_level || 'Mid-Level'}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Weekly Base
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {employee.standard_hours_per_week}h/wk
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Cost Rate
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  ${employee.cost_rate_per_hour || 75}/h
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Hire Date
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {employee.hire_date}
                </span>
              </div>
            </div>
          </div>

          {/* Professional Experience & Background Callout */}
          {(employee.experience_summary || employee.previous_company) && (
            <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs bg-slate-50/80 p-3 rounded-lg">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-blue-600 shrink-0" />
                <span className="font-medium text-slate-700">
                  {employee.previous_company ? (
                    <>Prior Organization: <span className="font-semibold text-slate-900">{employee.previous_company}</span></>
                  ) : (
                    'Professional Background'
                  )}
                </span>
              </div>
              {employee.experience_summary && (
                <p className="text-slate-600 italic text-[11px] max-w-xl">
                  "{employee.experience_summary}"
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs Navigation */}
      <Tabs tabs={profileTabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Skills Profile */}
      {activeTab === 'skills' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Skill Matrix & Proficiency</CardTitle>
              <CardDescription>
                Verified technical competencies, certifications, and proficiency ratings (1-5)
              </CardDescription>
            </div>
            <Button
              size="sm"
              variant="primary"
              icon={Plus}
              onClick={() => setIsAddSkillOpen(true)}
            >
              Add Skill
            </Button>
          </CardHeader>
          <CardContent>
            {skills.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No skill profiles linked to this employee yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {skills.map((s) => {
                  const isStale = s.verified_at && new Date(s.verified_at) < new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
                  return (
                    <div key={s.id} className="py-3.5 flex items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-xs text-slate-900">
                            {s.skill?.name || `Skill ID: ${s.skill_id}`}
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">
                            {s.skill?.category || 'General'}
                          </span>
                          {isStale && (
                            <Badge variant="warning" size="sm">
                              Stale Verification
                            </Badge>
                          )}
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500">
                          <span>Status: <strong>{s.verification_status}</strong></span>
                          <span>•</span>
                          <span>Last Verified: <strong>{s.verified_at || 'Never'}</strong></span>
                        </div>
                      </div>

                      {/* Proficiency Indicator (1 to 5) */}
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-mono font-bold text-slate-700 mr-1">
                          Lvl {s.proficiency_level}/5
                        </span>
                        {[1, 2, 3, 4, 5].map((lvl) => (
                          <span
                            key={lvl}
                            className={`h-2.5 w-4 rounded-xs ${
                              lvl <= s.proficiency_level ? 'bg-blue-600' : 'bg-slate-200'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Allocations */}
      {activeTab === 'allocations' && (
        <Card>
          <CardHeader>
            <CardTitle>Staffing & Project Allocations</CardTitle>
            <CardDescription>
              Committed delivery hours across active and pipeline client engagements
            </CardDescription>
          </CardHeader>
          <CardContent>
            {allocations.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No active project allocations recorded.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Project</th>
                      <th className="py-2.5 px-3">Allocation %</th>
                      <th className="py-2.5 px-3">Hours / Week</th>
                      <th className="py-2.5 px-3">Duration</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {allocations.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-semibold text-slate-900">
                          {a.project?.name || a.project_id}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-medium">
                          {a.allocation_percentage}%
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          {a.allocated_hours_per_week}h/wk
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 font-mono">
                          {a.start_date} → {a.end_date}
                        </td>
                        <td className="py-2.5 px-3">
                          <Badge
                            variant={
                              a.status === 'ACTIVE'
                                ? 'success'
                                : a.status === 'CONFIRMED'
                                ? 'primary'
                                : 'default'
                            }
                          >
                            {a.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Availability & Leave */}
      {activeTab === 'availability' && (
        <Card>
          <CardHeader>
            <CardTitle>Approved Leave & Availability Exceptions</CardTitle>
            <CardDescription>
              PTO, holidays, sick leave, and reserved capacity periods
            </CardDescription>
          </CardHeader>
          <CardContent>
            {availability.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                Full 100% standard availability. No leave deductions scheduled.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Leave Type</th>
                      <th className="py-2.5 px-3">Start Date</th>
                      <th className="py-2.5 px-3">End Date</th>
                      <th className="py-2.5 px-3">Deduction %</th>
                      <th className="py-2.5 px-3">Approval Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {availability.map((av) => (
                      <tr key={av.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">
                          {av.availability_type}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-600">{av.start_date}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-600">{av.end_date}</td>
                        <td className="py-2.5 px-3 font-mono">{100 - av.capacity_percentage}%</td>
                        <td className="py-2.5 px-3">
                          <Badge variant={av.is_approved ? 'success' : 'warning'}>
                            {av.is_approved ? 'APPROVED' : 'PENDING'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Utilization & Capacity */}
      {activeTab === 'utilization' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Live Capacity Calculation</CardTitle>
              <CardDescription>Net working hours after status & approved leave deductions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Base Contract Capacity</span>
                <span className="font-mono font-bold text-slate-800">
                  {capacity?.base_period_hours || employee.standard_hours_per_week * 4} hrs
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Leave Hours Deducted</span>
                <span className="font-mono font-bold text-amber-600">
                  -{capacity?.leave_hours_deducted || 0} hrs
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Net Working Capacity</span>
                <span className="font-mono font-bold text-blue-600">
                  {capacity?.net_available_hours || employee.standard_hours_per_week * 4} hrs
                </span>
              </div>
              <div className="flex justify-between py-2 text-xs">
                <span className="text-slate-500">Lifecycle Active Status</span>
                <Badge variant="success">Active in Period</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Workload Utilization Diagnostic</CardTitle>
              <CardDescription>Committed project allocations vs available working capacity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Total Allocated Hours</span>
                <span className="font-mono font-bold text-slate-800">
                  {utilization?.allocated_hours || 0} hrs
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Utilization Rate</span>
                <span className="font-mono font-bold text-slate-900 text-base">
                  {utilization?.utilization_percentage || 0}%
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100 text-xs">
                <span className="text-slate-500">Governance Category</span>
                <Badge
                  variant={
                    utilization?.is_overallocated
                      ? 'danger'
                      : utilization?.category === 'NORMAL'
                      ? 'success'
                      : 'default'
                  }
                >
                  {utilization?.category || 'NORMAL'}
                </Badge>
              </div>
              <div className="flex justify-between py-2 text-xs">
                <span className="text-slate-500">Overallocation Risk</span>
                <span className="font-bold text-xs">
                  {utilization?.is_overallocated ? (
                    <span className="text-rose-600">HIGH (Exceeds contract capacity)</span>
                  ) : (
                    <span className="text-emerald-600">NONE (Within limits)</span>
                  )}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 5: Training */}
      {activeTab === 'training' && (
        <Card>
          <CardHeader>
            <CardTitle>Upskilling & Career Track Progress</CardTitle>
            <CardDescription>
              Registered development programs to bridge upcoming project skill deficits
            </CardDescription>
          </CardHeader>
          <CardContent>
            {training.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No active training enrollments for this employee.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {training.map((t) => (
                  <div key={t.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-xs text-slate-900">{t.program_name}</div>
                      <div className="text-[11px] text-slate-500">
                        Provider: {t.provider || 'Internal Academy'} • Target Lvl: {t.target_proficiency}/5
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-slate-600">
                        {t.hours_per_week}h/wk • ${t.cost}
                      </span>
                      <Badge variant={t.status === 'COMPLETED' ? 'success' : 'primary'}>
                        {t.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Add Skill Modal */}
      <Modal
        isOpen={isAddSkillOpen}
        onClose={() => setIsAddSkillOpen(false)}
        title="Add Skill to Profile"
        description="Select a skill from taxonomy and specify assessed proficiency level."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsAddSkillOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleAddSkill}
              isLoading={isSavingSkill}
            >
              Add Skill
            </Button>
          </>
        }
      >
        <form onSubmit={handleAddSkill} className="space-y-3">
          <Select
            label="Select Skill"
            required
            value={skillForm.skill_id}
            onChange={(e) => setSkillForm({ ...skillForm, skill_id: e.target.value })}
          >
            <option value="">-- Choose Skill from Taxonomy --</option>
            {allSkillsTaxonomy.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.category})
              </option>
            ))}
          </Select>

          <Select
            label="Proficiency Level (1 - 5)"
            value={skillForm.proficiency_level}
            onChange={(e) => setSkillForm({ ...skillForm, proficiency_level: e.target.value })}
          >
            <option value="1">Level 1 - Fundamental Awareness</option>
            <option value="2">Level 2 - Novice / Working Knowledge</option>
            <option value="3">Level 3 - Intermediate / Autonomous</option>
            <option value="4">Level 4 - Advanced / Subject Matter Expert</option>
            <option value="5">Level 5 - Principal / Enterprise Authority</option>
          </Select>

          <Select
            label="Verification Status"
            value={skillForm.verification_status}
            onChange={(e) => setSkillForm({ ...skillForm, verification_status: e.target.value })}
          >
            <option value="VERIFIED">VERIFIED (Manager Approved)</option>
            <option value="CERTIFIED">CERTIFIED (Official Certificate)</option>
            <option value="SELF_REPORTED">SELF_REPORTED (Pending Verification)</option>
          </Select>

          <Input
            label="Verification Date"
            type="date"
            value={skillForm.verified_at}
            onChange={(e) => setSkillForm({ ...skillForm, verified_at: e.target.value })}
          />
        </form>
      </Modal>
    </div>
  );
}

export default EmployeeProfilePage;
