import React from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, XCircle } from 'lucide-react';
import Button from '../ui/Button';

export function ConnectionBanner({ isConnected, isDegraded, isError, onRetry, isRetrying }) {
  if (isConnected && !isDegraded) {
    return null; // Seamless when fully operational
  }

  if (isError) {
    return (
      <div className="bg-rose-50 border-b border-rose-200 px-4 py-2.5 sm:px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5 text-rose-800 text-sm font-medium">
            <XCircle className="h-4 w-4 text-rose-600 shrink-0" />
            <span>
              Unable to reach WorkforceIQ backend service at <code className="font-mono bg-rose-100/70 px-1 py-0.5 rounded text-xs">/api/v1</code>.
              Ensure the FastAPI server is running on port 8000.
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={onRetry}
            isLoading={isRetrying}
            className="border-rose-300 bg-white text-rose-700 hover:bg-rose-50 hover:text-rose-800"
          >
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  if (isDegraded) {
    return (
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 sm:px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5 text-amber-800 text-sm font-medium">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>
              System operational in development fallback mode. Target database connection is degraded or using SQLite fallback.
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={onRetry}
            isLoading={isRetrying}
            className="border-amber-300 bg-white text-amber-800 hover:bg-amber-100"
          >
            Refresh Diagnostics
          </Button>
        </div>
      </div>
    );
  }

  return null;
}

export default ConnectionBanner;

