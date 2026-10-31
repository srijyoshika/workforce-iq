import React from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Code2,
  Database,
  Layers,
  Lock,
  Server,
  ShieldCheck,
  TrendingUp,
  Users2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { StatusIndicator } from '../components/ui/StatusIndicator';

export function OverviewPage() {
  const { healthData, isError, clientLatencyMs } = useOutletContext();
  const isOnline = !isError && healthData !== null;

  const foundationDeliverables = [
    {
      title: 'FastAPI Backend Architecture',
      desc: 'Modular monolith structure with separated routers, services, schemas, and models. Zero business logic in controllers.',
      status: 'Operational',
      icon: Server,
    },
    {
      title: 'SQLAlchemy 2.0 Async Engine',
      desc: 'PostgreSQL connection pooling via asyncpg with automatic development fallback and zero hardcoded credentials.',
      status: 'Operational',
      icon: Database,
    },
    {
      title: 'React + Vite Frontend',
      desc: 'Modern enterprise SaaS user interface with Tailwind CSS, custom navy/slate palette, and responsive layouts.',
      status: 'Operational',
      icon: Code2,
    },
    {
      title: 'CORS & Security Controls',
      desc: 'Configured origin policies, Pydantic Settings environment parsing, and strict HTTP preflight verification.',
      status: 'Operational',
      icon: Lock,
    },
    {
      title: 'Live Telemetry & Diagnostics',
      desc: 'Real-time health check endpoint (/api/v1/health) measuring database latency, uptime, and host specs.',
      status: 'Operational',
      icon: Activity,
    },
    {
      title: 'Alembic Migration Pipeline',
      desc: 'Database schema migration environment configured with dynamic settings binding and version tracking.',
      status: 'Configured',
      icon: Layers,
    },
  ];

  const futureModules = [
    {
      title: 'Project Demand Forecasting',
      desc: 'Predict upcoming workforce requirements across upcoming initiatives using historical patterns and project scopes.',
      phase: 'Phase 2',
      icon: TrendingUp,
    },
    {
      title: 'Skill Gap Intelligence Engine',
      desc: 'Analyze inventory of organizational competencies, assess proficiency variances, and flag capability deficits.',
      phase: 'Phase 2',
      icon: BrainCircuit,
    },
    {
      title: 'Capacity & Utilization Analytics',
      desc: 'Calculate department-level workloads, detect burn-out thresholds, and identify under-utilized staff.',
      phase: 'Phase 2',
      icon: Users2,
    },
    {
      title: 'Optimal Staff Reallocation',
      desc: 'AI-assisted scenario simulator that generates optimal internal mobility, upskilling, and hiring paths.',
      phase: 'Phase 2',
      icon: BarChart3,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Platform Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-navy-950 via-navy-900 to-slate-900 p-8 text-white shadow-xl border border-navy-800">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs font-semibold text-blue-300 border border-blue-500/30">
              Phase 1 Deliverable Complete
            </span>
            <div className="flex items-center gap-1.5 text-xs text-slate-300">
              <StatusIndicator status={isOnline ? 'healthy' : 'offline'} size="sm" />
              <span>{isOnline ? 'API & Database Live' : 'Connecting to API...'}</span>
            </div>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            WorkforceIQ Intelligence Platform
          </h1>
          <p className="mt-3 text-base text-slate-300 leading-relaxed">
            Enterprise workforce planning system providing project demand forecasting, skill gap
            intelligence, capacity calculations, and AI staffing recommendations.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/health">
              <Button variant="primary" size="default" icon={Activity}>
                Inspect Live System Health
              </Button>
            </Link>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="default" className="text-white border-slate-700 bg-navy-800/80 hover:bg-navy-800">
                Explore FastAPI Swagger Docs
              </Button>
            </a>
          </div>
        </div>
      </div>

      {/* Architectural Readiness Grid */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900">
            System Architecture & Foundation Deliverables
          </h2>
          <p className="text-xs text-slate-500">
            All Phase 1 foundational requirements have been implemented according to enterprise standards.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {foundationDeliverables.map((item, idx) => {
            const Icon = item.icon;
            return (
              <Card key={idx} className="hover:border-slate-300 transition-all">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-700 border border-blue-100">
                      <Icon className="h-4 w-4" />
                    </div>
                    <Badge variant="success" size="sm">
                      {item.status}
                    </Badge>
                  </div>
                  <CardTitle className="text-sm font-semibold text-slate-900 mt-2">
                    {item.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Future Intelligence Modules Roadmap (Unfaked) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold tracking-tight text-slate-900">
              Intelligence Modules Roadmap
            </h2>
            <p className="text-xs text-slate-500">
              Scheduled for implementation in Phase 2 upon foundation sign-off. No simulated or mock data is injected.
            </p>
          </div>
          <span className="text-xs font-mono font-medium text-slate-400 bg-slate-100 px-2.5 py-1 rounded-md">
            Phase 2 Scope
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {futureModules.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-200/60 text-slate-500">
                    <Icon className="h-4 w-4" />
                  </div>
                  <Badge variant="default" size="sm">
                    {item.phase}
                  </Badge>
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-800">{item.title}</h3>
                  <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default OverviewPage;

