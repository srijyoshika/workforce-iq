import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  Users,
  Briefcase,
  TrendingUp,
  BrainCircuit,
  Sliders,
  Calendar,
  Layers,
  GraduationCap,
  Sparkles,
  Zap,
  AlertTriangle,
  CheckCircle,
  Shield,
  Settings,
  History,
} from 'lucide-react';
import { Modal } from '../ui/Modal';
import { workforceApi } from '../../api/workforce';
import { planningApi } from '../../api/planning';

const STATIC_PAGES = [
  { name: 'Executive Dashboard', path: '/dashboard', icon: LayoutDashboard, category: 'Core' },
  { name: 'Employee Directory', path: '/employees', icon: Users, category: 'Workforce' },
  { name: 'Roles & Skills Taxonomy', path: '/roles-skills', icon: Briefcase, category: 'Workforce' },
  { name: 'Availability & Leave', path: '/availability', icon: Calendar, category: 'Workforce' },
  { name: 'Training Management', path: '/training', icon: GraduationCap, category: 'Workforce' },
  { name: 'Project Management', path: '/projects', icon: Briefcase, category: 'Planning' },
  { name: 'Demand Forecast', path: '/forecast', icon: TrendingUp, category: 'Planning' },
  { name: 'Resource Allocations', path: '/allocations', icon: Layers, category: 'Planning' },
  { name: 'Skill Gap Analysis', path: '/skill-gaps', icon: BrainCircuit, category: 'Planning' },
  { name: 'Workforce Utilization', path: '/utilization', icon: Sliders, category: 'Planning' },
  { name: 'Hiring Recommendations', path: '/recommendations', icon: Sparkles, category: 'Intelligence' },
  { name: 'Resource Optimization', path: '/optimization', icon: Zap, category: 'Intelligence' },
  { name: 'Scenario Planning', path: '/scenarios', icon: Sliders, category: 'Intelligence' },
  { name: 'Exception Monitoring', path: '/exceptions', icon: AlertTriangle, category: 'Governance' },
  { name: 'Data Quality & Evaluation', path: '/quality', icon: CheckCircle, category: 'Governance' },
  { name: 'Audit History', path: '/audit', icon: History, category: 'Governance' },
  { name: 'Administration', path: '/admin', icon: Settings, category: 'Governance' },
];

export function GlobalSearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const [employees, setEmployees] = useState([]);
  const [projects, setProjects] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!query || query.length < 2) {
      setEmployees([]);
      setProjects([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const [empRes, prjRes] = await Promise.allSettled([
          workforceApi.listEmployees({ search: query, page_size: 5 }),
          planningApi.listProjects({ search: query, page_size: 5 }),
        ]);

        if (empRes.status === 'fulfilled') {
          setEmployees(empRes.value?.items || []);
        }
        if (prjRes.status === 'fulfilled') {
          setProjects(prjRes.value?.items || []);
        }
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (path) => {
    onClose();
    setQuery('');
    navigate(path);
  };

  const filteredPages = STATIC_PAGES.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Global Platform Search" maxWidth="max-w-2xl">
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search pages, employees, projects, or skills (e.g., 'Python', 'John', 'Forecast')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-3 text-sm focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-slate-50/50"
          />
        </div>

        <div className="max-h-96 overflow-y-auto space-y-4 divide-y divide-slate-100">
          {/* Quick Page Jump */}
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Platform Modules
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {filteredPages.slice(0, 8).map((page) => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.path}
                    type="button"
                    onClick={() => handleSelect(page.path)}
                    className="flex items-center gap-2.5 rounded-lg p-2 text-left hover:bg-slate-100 transition-colors group"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-100 text-slate-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-800">{page.name}</div>
                      <div className="text-[10px] text-slate-400">{page.category}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Employee Results */}
          {employees.length > 0 && (
            <div className="pt-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                Employees
              </p>
              <div className="space-y-1">
                {employees.map((emp) => (
                  <button
                    key={emp.id}
                    type="button"
                    onClick={() => handleSelect(`/employees/${emp.id}`)}
                    className="flex w-full items-center justify-between rounded-lg p-2 hover:bg-slate-100 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-bold text-xs font-mono">
                        {emp.first_name[0]}
                        {emp.last_name[0]}
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-900">
                          {emp.first_name} {emp.last_name}
                        </span>
                        <span className="ml-2 font-mono text-[11px] text-slate-400">
                          {emp.business_id}
                        </span>
                      </div>
                    </div>
                    <span className="text-xs text-slate-500">{emp.department}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Project Results */}
          {projects.length > 0 && (
            <div className="pt-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                Projects
              </p>
              <div className="space-y-1">
                {projects.map((prj) => (
                  <button
                    key={prj.id}
                    type="button"
                    onClick={() => handleSelect('/projects')}
                    className="flex w-full items-center justify-between rounded-lg p-2 hover:bg-slate-100 transition-colors text-left"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-900">{prj.name}</div>
                      <div className="text-[10px] font-mono text-slate-400">{prj.code} • {prj.business_id}</div>
                    </div>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                      {prj.status}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {query && !isSearching && filteredPages.length === 0 && employees.length === 0 && projects.length === 0 && (
            <div className="py-6 text-center text-xs text-slate-500">
              No matching records found for "{query}".
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}

export default GlobalSearchModal;
