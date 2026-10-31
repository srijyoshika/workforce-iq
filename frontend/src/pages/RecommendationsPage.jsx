import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  RefreshCw,
  UserPlus,
  GraduationCap,
  Layers,
  Calendar,
  CheckCircle2,
  DollarSign,
  Clock,
  Award,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { intelligenceApi } from '../api/intelligence';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import KpiStatCard from '../components/ui/KpiStatCard';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [filterAction, setFilterAction] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  const fetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await intelligenceApi.generateRecommendations({ max_recommendations: 20 });
      setRecommendations(res.recommendations || []);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setRecommendations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const filteredRecs = recommendations.filter((r) => {
    if (filterAction === 'ALL') return true;
    return r.action_type === filterAction;
  });

  const hiringCount = recommendations.filter((r) => r.action_type === 'HIRE').length;
  const trainingCount = recommendations.filter((r) => r.action_type === 'TRAIN').length;
  const reallocateCount = recommendations.filter((r) => r.action_type === 'REALLOCATE').length;
  const rescheduleCount = recommendations.filter((r) => r.action_type === 'RESCHEDULE').length;

  const getActionBadge = (actionType) => {
    switch (actionType) {
      case 'HIRE':
        return <Badge variant="primary">HIRE (External Recruitment)</Badge>;
      case 'TRAIN':
        return <Badge variant="teal">TRAIN (Internal Upskilling)</Badge>;
      case 'REALLOCATE':
        return <Badge variant="purple">REALLOCATE (Cross-Staffing)</Badge>;
      case 'RESCHEDULE':
        return <Badge variant="warning">RESCHEDULE (Timeline Shift)</Badge>;
      default:
        return <Badge variant="default">{actionType}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Staffing & Hiring Recommendations Engine
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Explainable AI decision intelligence: automated trade-offs between Reallocation, Training, Hiring, and Rescheduling.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={fetchRecommendations}
            isLoading={isLoading}
            icon={Sparkles}
          >
            Generate Recommendations
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiStatCard
          title="Hire Recommendations"
          value={isLoading ? '...' : hiringCount.toString()}
          subtitle="New headcounts needed"
          icon={UserPlus}
          accent="blue"
        />
        <KpiStatCard
          title="Train Internal Staff"
          value={isLoading ? '...' : trainingCount.toString()}
          subtitle="Targeted upskilling paths"
          icon={GraduationCap}
          accent="teal"
        />
        <KpiStatCard
          title="Reallocate Resources"
          value={isLoading ? '...' : reallocateCount.toString()}
          subtitle="Optimized bench movement"
          icon={Layers}
          accent="purple"
        />
        <KpiStatCard
          title="Reschedule Milestones"
          value={isLoading ? '...' : rescheduleCount.toString()}
          subtitle="Deferred non-critical work"
          icon={Calendar}
          accent="amber"
        />
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {['ALL', 'HIRE', 'TRAIN', 'REALLOCATE', 'RESCHEDULE'].map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => setFilterAction(action)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                filterAction === action
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {action}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Showing {filteredRecs.length} Action Plans
        </span>
      </div>

      {/* Recommendations Cards List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-400">
            Evaluating capability matrices and calculating optimal resolutions...
          </div>
        ) : filteredRecs.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-500">
            No recommendations generated for the selected action filter.
          </div>
        ) : (
          filteredRecs.map((rec) => {
            const isExpanded = expandedId === rec.gap_id;
            return (
              <Card key={rec.gap_id || Math.random()} className="overflow-hidden">
                <div
                  className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
                  onClick={() => setExpandedId(isExpanded ? null : rec.gap_id)}
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {getActionBadge(rec.action_type)}
                      <span className="font-mono text-xs font-semibold text-slate-900">
                        {rec.required_skill || 'Enterprise Skill'}
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-xs text-slate-500 font-mono">
                        Gap ID: {rec.gap_id}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 font-medium">
                      {rec.explanation || 'Optimal staffing resolution based on cost and lead-time constraints.'}
                    </p>
                  </div>

                  {/* Summary Metrics Pill */}
                  <div className="flex items-center gap-4 self-end sm:self-auto text-xs shrink-0">
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Estimated Cost
                      </span>
                      <span className="font-mono font-bold text-slate-900">
                        ${Number(rec.expected_cost || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Resolution Time
                      </span>
                      <span className="font-mono font-bold text-teal-600">
                        {rec.estimated_time_to_resolve_days || 14} days
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Suitability
                      </span>
                      <span className="font-mono font-bold text-blue-600">
                        {Math.round((rec.confidence_score || 0.85) * 100)}%
                      </span>
                    </div>

                    <button
                      type="button"
                      className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
                    >
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Explanations and Assumptions Drawer */}
                {isExpanded && (
                  <div className="bg-slate-50/80 border-t border-slate-100 p-5 space-y-3 text-xs">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                          Key Decision Assumptions
                        </span>
                        <p className="text-slate-600 bg-white p-3 rounded-lg border border-slate-200">
                          {rec.assumptions || 'Assumes standard hiring lead time of 45 days and prevailing market hourly contract rates.'}
                        </p>
                      </div>

                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                          Affected Employees & Delivery Impact
                        </span>
                        <div className="bg-white p-3 rounded-lg border border-slate-200 space-y-1 font-mono text-[11px]">
                          <div>Shortage Hours Reduced: <strong className="text-emerald-600">{rec.expected_shortage_reduction || 40} hrs</strong></div>
                          <div>Deadline Feasible: <strong className={rec.deadline_feasible ? 'text-emerald-600' : 'text-rose-600'}>{rec.deadline_feasible ? 'YES' : 'NO'}</strong></div>
                          <div>Governance Rule Version: <strong className="text-slate-700">{rec.rule_version || 'v2.1'}</strong></div>
                        </div>
                      </div>
                    </div>

                    {/* Manager Approval Actions */}
                    <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">
                        Manager Action: Approval will update operational state and log audit trail.
                      </span>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 text-xs text-rose-600 hover:bg-rose-50 border-rose-200"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              await intelligenceApi.rejectRecommendation(rec.gap_id || 'REC-1');
                              alert(`Recommendation for '${rec.required_skill}' rejected.`);
                            } catch (err) {
                              alert(`Rejection error: ${err.message}`);
                            }
                          }}
                        >
                          Reject Proposal
                        </Button>
                        <Button
                          size="sm"
                          variant="primary"
                          className="h-8 text-xs bg-emerald-600 hover:bg-emerald-700"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              await intelligenceApi.approveRecommendation(rec.gap_id || 'REC-1');
                              alert(`Recommendation for '${rec.required_skill}' approved and logged to audit trail.`);
                            } catch (err) {
                              alert(`Approval error: ${err.message}`);
                            }
                          }}
                        >
                          Approve Recommendation
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

export default RecommendationsPage;
