import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, AlertTriangle, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { intelligenceApi } from '../../api/intelligence';
import Badge from '../ui/Badge';

export function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const [issues, setIssues] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    async function fetchAlerts() {
      try {
        const res = await intelligenceApi.listIssues({ status: 'OPEN', page_size: 5 });
        if (isMounted) {
          setIssues(res.items || []);
          setTotalCount(res.total || 0);
        }
      } catch (err) {
        // Silently catch in topbar notification polling
      }
    }

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // 30s poll

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors focus:outline-none"
        title="Exception & Risk Notifications"
        aria-label="Exception notifications"
      >
        <Bell className="h-5 w-5" />
        {totalCount > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow-sm ring-2 ring-white">
            {totalCount > 9 ? '9+' : totalCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-slate-200 bg-white shadow-2xl z-50 overflow-hidden divide-y divide-slate-100 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="p-4 flex items-center justify-between bg-slate-50/70">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Exception Alerts
              </span>
              <Badge variant={totalCount > 0 ? 'danger' : 'success'} size="sm">
                {totalCount} Active
              </Badge>
            </div>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate('/exceptions');
              }}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {issues.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                <span>Zero unresolved workforce exceptions detected.</span>
              </div>
            ) : (
              issues.map((issue) => (
                <div
                  key={issue.id}
                  onClick={() => {
                    setIsOpen(false);
                    navigate('/exceptions');
                  }}
                  className="p-3.5 hover:bg-slate-50 transition-colors cursor-pointer flex items-start gap-3"
                >
                  <div className="mt-0.5">
                    {issue.severity === 'CRITICAL' || issue.severity === 'HIGH' ? (
                      <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-slate-900 truncate">
                        {issue.title}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 shrink-0">
                        {issue.issue_type}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">
                      {issue.description}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>

          {totalCount > 0 && (
            <div className="p-2.5 bg-slate-50/50 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  navigate('/exceptions');
                }}
                className="text-xs font-semibold text-slate-700 hover:text-blue-600"
              >
                Inspect All Exceptions in Anomaly Registry
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationDropdown;
