import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const ROUTE_LABELS = {
  dashboard: 'Executive Dashboard',
  employees: 'Employee Directory',
  'roles-skills': 'Roles & Skills Taxonomy',
  projects: 'Project Management',
  forecast: 'Demand Forecast',
  allocations: 'Resource Allocations',
  availability: 'Availability & Leave',
  'skill-gaps': 'Skill Gap Analysis',
  utilization: 'Workforce Utilization',
  training: 'Training Management',
  recommendations: 'Hiring & Staffing Recommendations',
  optimization: 'Resource Optimization Engine',
  scenarios: 'Scenario Planning & Simulation',
  exceptions: 'Exception & Anomaly Monitoring',
  quality: 'Data Quality & Evaluation',
  audit: 'Audit Event History',
  admin: 'System Administration',
  health: 'System Diagnostics',
};

export function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter(Boolean);

  if (pathnames.length === 0) return null;

  return (
    <nav className="flex items-center text-xs text-slate-500 mb-4" aria-label="Breadcrumb">
      <Link
        to="/dashboard"
        className="flex items-center text-slate-400 hover:text-slate-700 transition-colors"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>

      {pathnames.map((segment, idx) => {
        const routeTo = `/${pathnames.slice(0, idx + 1).join('/')}`;
        const isLast = idx === pathnames.length - 1;
        const label = ROUTE_LABELS[segment] || segment;

        return (
          <React.Fragment key={routeTo}>
            <ChevronRight className="h-3.5 w-3.5 mx-1.5 text-slate-300 shrink-0" />
            {isLast ? (
              <span className="font-semibold text-slate-900 truncate max-w-xs">{label}</span>
            ) : (
              <Link to={routeTo} className="hover:text-slate-900 transition-colors">
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

export default Breadcrumbs;
