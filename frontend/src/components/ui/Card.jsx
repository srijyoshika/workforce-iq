import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Card({ className = '', children, ...props }) {
  return (
    <div
      className={twMerge(
        clsx('rounded-xl border border-slate-200/90 bg-white shadow-card transition-all', className)
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className = '', children, ...props }) {
  return (
    <div className={twMerge(clsx('flex flex-col space-y-1.5 p-6 border-b border-slate-100', className))} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className = '', children, ...props }) {
  return (
    <h3
      className={twMerge(
        clsx('text-base font-semibold leading-none tracking-tight text-slate-900', className)
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ className = '', children, ...props }) {
  return (
    <p className={twMerge(clsx('text-sm text-slate-500', className))} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ className = '', children, ...props }) {
  return (
    <div className={twMerge(clsx('p-6', className))} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className = '', children, ...props }) {
  return (
    <div
      className={twMerge(clsx('flex items-center p-6 pt-0 border-t border-slate-100 mt-4', className))}
      {...props}
    >
      {children}
    </div>
  );
}

