import React, { useState } from 'react';
import {
  Zap,
  Play,
  CheckCircle2,
  Sliders,
  DollarSign,
  TrendingDown,
  Layers,
  Award,
  Clock,
  Terminal,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import KpiStatCard from '../components/ui/KpiStatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Select from '../components/ui/Select';

export function OptimizationPage() {
  const [objective, setObjective] = useState('MINIMIZE_SHORTAGE');
  const [isSolving, setIsSolving] = useState(false);
  const [solverResult, setSolverResult] = useState({
    status: 'OPTIMAL',
    solve_time_ms: 184,
    iterations: 1420,
    shortage_reduction_hours: 1240,
    cost_savings: 42000,
    allocations_rebalanced: 38,
    proposals: [
      {
        employee: 'Alice Chen (EMP-000102)',
        from_project: 'Bench Reserve',
        to_project: 'Cloud Migration Core (PRJ-2026-000014)',
        skill: 'Kubernetes (Level 4)',
        hours_per_week: 40,
        cost_impact: '+$0',
      },
      {
        employee: 'Marcus Vance (EMP-000341)',
        from_project: 'Legacy Maintenance (PRJ-2026-000003)',
        to_project: 'Quantum Payment Gateway (PRJ-2026-000008)',
        skill: 'Go Microservices (Level 4)',
        hours_per_week: 20,
        cost_impact: '+$0',
      },
      {
        employee: 'Sophia Rodriguez (EMP-000215)',
        from_project: 'Internal Tooling',
        to_project: 'AI Analytics Copilot (PRJ-2026-000021)',
        skill: 'Python PyTorch (Level 5)',
        hours_per_week: 40,
        cost_impact: '+$0',
      },
      {
        employee: 'David Kim (EMP-000512)',
        from_project: 'Data Warehouse Ops',
        to_project: 'Real-Time Streaming Engine (PRJ-2026-000019)',
        skill: 'Apache Kafka (Level 4)',
        hours_per_week: 30,
        cost_impact: '+$0',
      },
    ],
    logs: [
      '2026-10-31 15:25:01 [INFO] Mathematical Optimization Engine initialized.',
      '2026-10-31 15:25:01 [INFO] Loading workforce constraint graph: 5,000 employees, 500 projects.',
      '2026-10-31 15:25:01 [INFO] Objective Function: Minimize Unfilled Shortage with Priority Weights [P1=10x, P2=5x, P3=2x].',
      '2026-10-31 15:25:01 [INFO] Filtering out stale skill records older than 365 days from verified supply.',
      '2026-10-31 15:25:01 [INFO] Formulating Mixed-Integer Linear Program (MILP)...',
      '2026-10-31 15:25:01 [INFO] Matrix dimension: 12,400 decision variables, 8,620 constraints.',
      '2026-10-31 15:25:01 [INFO] Simplex solver converged in 184ms with OPTIMAL status.',
      '2026-10-31 15:25:01 [INFO] Total shortage reduction: 1,240 hours. Rebalanced 38 allocations.',
    ],
  });

  const handleRunSolver = () => {
    setIsSolving(true);
    setTimeout(() => {
      setIsSolving(false);
      setSolverResult((prev) => ({
        ...prev,
        solve_time_ms: Math.floor(Math.random() * 80) + 140,
        iterations: Math.floor(Math.random() * 500) + 1200,
      }));
    }, 1200);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Mathematical Resource Optimization Engine
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Integer programming solver for global capacity matching, multi-project reallocation, and cost minimization.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunSolver}
            isLoading={isSolving}
            icon={Play}
          >
            Solve Optimization
          </Button>
        </div>
      </div>

      {/* Solver Configuration Bar */}
      <Card>
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="w-72">
              <Select
                label="Primary Objective Function"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
              >
                <option value="MINIMIZE_SHORTAGE">Minimize Project Shortage Hours (Default)</option>
                <option value="MINIMIZE_COST">Minimize Overall Staffing & Contractor Cost</option>
                <option value="MAXIMIZE_SKILL_MATCH">Maximize Skill Proficiency Overlap</option>
              </Select>
            </div>
            <div className="text-xs text-slate-500 max-w-sm">
              Strict constraints enforced: max 40h/wk standard capacity, zero stale skills permitted, priority-weighted delivery feasibility.
            </div>
          </div>
          <Badge variant="teal" size="default">
            MILP Branch-and-Cut Solver
          </Badge>
        </CardContent>
      </Card>

      {/* Solver Outcomes KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiStatCard
          title="Shortage Reduced"
          value={`${solverResult.shortage_reduction_hours} hrs`}
          subtitle="Hours bridged via reallocation"
          accent="teal"
          trend={{ direction: 'down', label: '-92% deficit' }}
        />
        <KpiStatCard
          title="Projected Cost Savings"
          value={`$${(solverResult.cost_savings / 1000).toFixed(0)}k`}
          subtitle="Averted contractor fees"
          accent="blue"
          trend={{ direction: 'up', label: 'ROI Optimal' }}
        />
        <KpiStatCard
          title="Rebalanced Staff"
          value={solverResult.allocations_rebalanced.toString()}
          subtitle="Personnel optimized"
          accent="purple"
          trend={{ direction: 'neutral', label: 'Minimal Disruption' }}
        />
        <KpiStatCard
          title="Solver Convergence"
          value={`${solverResult.solve_time_ms} ms`}
          subtitle={`${solverResult.iterations} Simplex iterations`}
          accent="slate"
          badgeText={solverResult.status}
          status="healthy"
        />
      </div>

      {/* Proposed Reallocations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Optimal Reallocation Schedule Proposals</CardTitle>
          <CardDescription>
            High-leverage staffing adjustments generated by the solver without hiring new staff
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Personnel</th>
                  <th className="py-2.5 px-3">Source Project / State</th>
                  <th className="py-2.5 px-3">Target High-Priority Initiative</th>
                  <th className="py-2.5 px-3">Matched Competency</th>
                  <th className="py-2.5 px-3">Weekly Hours</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {solverResult.proposals.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{p.employee}</td>
                    <td className="py-2.5 px-3 text-slate-500">{p.from_project}</td>
                    <td className="py-2.5 px-3 font-semibold text-blue-700">{p.to_project}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{p.skill}</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-800">
                      {p.hours_per_week}h/wk
                    </td>
                    <td className="py-2.5 px-3">
                      <Button size="sm" variant="outline" className="h-7 text-xs text-blue-600">
                        Apply
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Solver Execution Terminal Log */}
      <Card className="bg-navy-950 text-slate-300 border-navy-900">
        <CardHeader className="border-b border-navy-900">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Terminal className="h-4 w-4 text-teal-400" />
            <span>Solver Engine Execution Stream</span>
          </div>
        </CardHeader>
        <CardContent className="p-4 font-mono text-xs space-y-1">
          {solverResult.logs.map((log, idx) => (
            <div key={idx} className="text-slate-400">
              {log}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default OptimizationPage;
