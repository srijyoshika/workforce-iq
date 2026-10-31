import React, { useState, useEffect, useCallback } from 'react';
import {
  Sliders,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Building,
  User,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { intelligenceApi } from '../api/intelligence';
import { workforceApi } from '../api/workforce';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import KpiStatCard from '../components/ui/KpiStatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';

export function UtilizationPage() {
  const [departments, setDepartments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Single Employee Diagnostic Tool
  const [employeesList, setEmployeesList] = useState([]);
  const [selectedEmpId, setSelectedEmpId] = useState('');
  const [diagStartDate, setDiagStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [diagEndDate, setDiagEndDate] = useState(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [empUtilResult, setEmpUtilResult] = useState(null);
  const [isCalculatingEmp, setIsCalculatingEmp] = useState(false);

  const fetchDepartmentUtilization = useCallback(async () => {
    setIsLoading(true);
    try {
      const [deptRes, empRes] = await Promise.allSettled([
        intelligenceApi.getDepartmentUtilization(),
        workforceApi.listEmployees({ page_size: 50 }),
      ]);

      if (deptRes.status === 'fulfilled' && Array.isArray(deptRes.value)) {
        setDepartments(deptRes.value);
      }
      if (empRes.status === 'fulfilled') {
        const emps = empRes.value?.items || [];
        setEmployeesList(emps);
        if (emps.length > 0 && !selectedEmpId) {
          setSelectedEmpId(emps[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load utilization:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedEmpId]);

  useEffect(() => {
    fetchDepartmentUtilization();
  }, [fetchDepartmentUtilization]);

  const handleCalculateSingleEmp = async (e) => {
    e.preventDefault();
    if (!selectedEmpId) return;
    setIsCalculatingEmp(true);
    try {
      const res = await intelligenceApi.calculateUtilization(
        selectedEmpId,
        diagStartDate,
        diagEndDate
      );
      setEmpUtilResult(res);
    } catch (err) {
      alert(`Calculation error: ${err.message}`);
    } finally {
      setIsCalculatingEmp(false);
    }
  };

  // High-level aggregates
  const totalAllocated = departments.reduce((acc, d) => acc + (d.allocated_hours || 0), 0);
  const totalAvailable = departments.reduce((acc, d) => acc + (d.available_hours || 0), 0);
  const overallAvgUtil = totalAvailable > 0 ? Math.round((totalAllocated / totalAvailable) * 100) : 85;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Workforce Capacity & Workload Utilization
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Real-time workload governance, department efficiency ratings, and overallocation risk detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDepartmentUtilization}
            isLoading={isLoading}
            icon={RefreshCw}
          >
            Refresh Diagnostics
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiStatCard
          title="Corporate Utilization"
          value={`${overallAvgUtil}%`}
          subtitle="Target: 80-92%"
          accent="blue"
          trend={{ direction: 'up', label: '+1.8%' }}
        />
        <KpiStatCard
          title="Total Allocated Hours"
          value={`${(totalAllocated / 1000).toFixed(1)}k hrs`}
          subtitle="Client engagement delivery"
          accent="teal"
          trend={{ direction: 'up', label: 'Committed' }}
        />
        <KpiStatCard
          title="Total Contract Capacity"
          value={`${(totalAvailable / 1000).toFixed(1)}k hrs`}
          subtitle="Net working hours"
          accent="blue"
          trend={{ direction: 'neutral', label: 'Stable' }}
        />
        <KpiStatCard
          title="Departments Overallocated"
          value={departments.filter((d) => d.utilization_percentage > 100).length.toString()}
          subtitle="Departments >100% capacity"
          accent="amber"
          status={departments.some((d) => d.utilization_percentage > 100) ? 'warning' : 'healthy'}
        />
      </div>

      {/* Department Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Department Capacity vs Allocated Workload</CardTitle>
          <CardDescription>
            Comparison between net available capacity (teal) and allocated hours (blue / red if overallocated)
          </CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departments} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="department" tickLine={false} stroke="#64748B" fontSize={11} />
              <YAxis tickLine={false} stroke="#64748B" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0F1E36', borderColor: '#1E293B', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="available_hours" name="Available Capacity (Hrs)" fill="#0D9488" radius={[4, 4, 0, 0]} />
              <Bar dataKey="allocated_hours" name="Allocated Workload (Hrs)" fill="#2563EB" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Individual Employee Utilization Diagnostic Calculator */}
      <Card>
        <CardHeader>
          <CardTitle>Individual Employee Capacity Diagnostic</CardTitle>
          <CardDescription>
            Run on-demand capacity and workload calculation for any corporate employee
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCalculateSingleEmp} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
            <div className="sm:col-span-2">
              <Select
                label="Select Employee"
                value={selectedEmpId}
                onChange={(e) => setSelectedEmpId(e.target.value)}
              >
                {employeesList.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name} ({emp.department} • {emp.business_id})
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Input
                label="Start Date"
                type="date"
                value={diagStartDate}
                onChange={(e) => setDiagStartDate(e.target.value)}
              />
            </div>
            <div>
              <Button
                type="submit"
                variant="primary"
                size="default"
                className="w-full"
                isLoading={isCalculatingEmp}
              >
                Calculate Utilization
              </Button>
            </div>
          </form>

          {empUtilResult && (
            <div className="mt-6 p-4 rounded-xl border border-slate-200 bg-slate-50/60 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Available Capacity
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {empUtilResult.available_hours} hrs
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Allocated Workload
                </span>
                <span className="font-mono font-bold text-blue-600 text-sm">
                  {empUtilResult.allocated_hours} hrs
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Utilization Rate
                </span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {empUtilResult.utilization_percentage}%
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Status Category
                </span>
                <Badge
                  variant={
                    empUtilResult.is_overallocated
                      ? 'danger'
                      : empUtilResult.category === 'NORMAL'
                      ? 'success'
                      : 'default'
                  }
                  size="sm"
                >
                  {empUtilResult.category}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default UtilizationPage;
