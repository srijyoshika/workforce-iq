import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function StatusIndicator({
  status = 'healthy', // healthy | degraded | offline | warning | info
  size = 'md', // sm | md | lg
  pulse = true,
  className = '',
}) {
  const statusColor = {
    healthy: 'bg-emerald-500',
    operational: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    warning: 'bg-amber-500',
    offline: 'bg-rose-500',
    unhealthy: 'bg-rose-500',
    info: 'bg-blue-500',
  }[status] || 'bg-slate-400';

  const sizeMap = {
    sm: 'h-2 w-2',
    md: 'h-2.5 w-2.5',
    lg: 'h-3.5 w-3.5',
  };

  const pingSizeMap = {
    sm: 'h-2 w-2',
    md: 'h-2.5 w-2.5',
    lg: 'h-3.5 w-3.5',
  };

  return (
    <span className={twMerge(clsx('relative inline-flex items-center justify-center', className))}>
      {pulse && (
        <span
          className={clsx(
            'absolute inline-flex rounded-full opacity-75 animate-ping',
            statusColor,
            pingSizeMap[size]
          )}
        />
      )}
      <span className={clsx('relative inline-flex rounded-full', statusColor, sizeMap[size])} />
    </span>
  );
}

export default StatusIndicator;

