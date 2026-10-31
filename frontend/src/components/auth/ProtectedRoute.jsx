import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { CardSkeleton } from '../ui/Skeleton';

export function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, isLoading, hasRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !hasRole(...allowedRoles)) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center space-y-4">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6">
          <h2 className="text-base font-bold text-rose-800">Access Restricted</h2>
          <p className="mt-2 text-xs text-rose-600">
            Your user account does not possess the requisite organizational role to view this module.
          </p>
        </div>
      </div>
    );
  }

  return children;
}

export default ProtectedRoute;
