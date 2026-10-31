import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Badge({ children, variant = 'default', size = 'default', className = '', ...props }) {
  const baseStyles = 'inline-flex items-center font-medium rounded-full transition-colors select-none tracking-tight';

  const variants = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    primary: 'bg-blue-50 text-blue-700 border border-blue-200',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border border-rose-200',
    critical: 'bg-red-100 text-red-800 border border-red-300 font-bold animate-pulse',
    teal: 'bg-teal-50 text-teal-700 border border-teal-200',
    purple: 'bg-purple-50 text-purple-700 border border-purple-200',
    navy: 'bg-navy-900 text-white',
    live: 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20',
    ready: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
    offline: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    default: 'px-2.5 py-0.5 text-xs font-semibold',
    lg: 'px-3 py-1 text-sm',
  };

  return (
    <span className={twMerge(clsx(baseStyles, variants[variant] || variants.default, sizes[size] || sizes.default, className))} {...props}>
      {children}
    </span>
  );
}

export default Badge;
