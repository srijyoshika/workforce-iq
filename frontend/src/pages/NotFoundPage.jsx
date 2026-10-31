import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import Button from '../components/ui/Button';

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-4">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h2 className="text-xl font-bold text-slate-900">Resource Not Found</h2>
      <p className="mt-2 text-sm text-slate-500 max-w-sm">
        The requested platform route does not exist or has not been activated.
      </p>
      <div className="mt-6">
        <Link to="/">
          <Button variant="default" size="default" icon={ArrowLeft}>
            Return to Overview
          </Button>
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;

