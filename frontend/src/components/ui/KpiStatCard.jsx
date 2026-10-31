import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { StatusIndicator } from './StatusIndicator';

export function KpiStatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  status = 'healthy',
  badgeText,
  trend, // { direction: 'up' | 'down' | 'neutral', label: string }
  accent = 'blue', // 'blue' | 'teal' | 'amber' | 'rose' | 'slate'
  className = '',
}) {
  const accentBorders = {
    blue: 'border-l-4 border-l-blue-600',
    teal: 'border-l-4 border-l-teal-500',
    amber: 'border-l-4 border-l-amber-500',
    rose: 'border-l-4 border-l-rose-500',
    slate: 'border-l-4 border-l-slate-400',
  };

  const iconBg = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    teal: 'bg-teal-50 text-teal-600 border-teal-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    slate: 'bg-slate-50 text-slate-600 border-slate-100',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-5 shadow-card hover:shadow-elevated transition-all flex flex-col justify-between',
          accentBorders[accent] || '',
          className
        )
      )}
    >
      <div>
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
          {Icon && (
            <div className={clsx('flex h-9 w-9 items-center justify-center rounded-lg border', iconBg[accent] || iconBg.blue)}>
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline justify-between gap-2">
          <div className="text-2xl font-bold tracking-tight text-slate-900 font-mono">{value}</div>
          {badgeText && (
            <div className="flex items-center gap-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
              <StatusIndicator status={status} size="sm" pulse={status === 'healthy'} />
              <span>{badgeText}</span>
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-slate-100/80 flex items-center justify-between text-xs">
        {subtitle && <span className="text-slate-500 font-medium truncate">{subtitle}</span>}
        {trend && (
          <span
            className={clsx(
              'inline-flex items-center gap-0.5 font-semibold font-mono',
              trend.direction === 'up' && 'text-emerald-600',
              trend.direction === 'down' && 'text-rose-600',
              trend.direction === 'neutral' && 'text-slate-500'
            )}
          >
            {trend.direction === 'up' && <TrendingUp className="h-3.5 w-3.5" />}
            {trend.direction === 'down' && <TrendingDown className="h-3.5 w-3.5" />}
            {trend.direction === 'neutral' && <Minus className="h-3.5 w-3.5" />}
            {trend.label}
          </span>
        )}
      </div>
    </div>
  );
}

export default KpiStatCard;
