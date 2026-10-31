import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { BarChart3, Lock, Mail, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

export function LoginPage() {
  const [email, setEmail] = useState('admin@workforceiq.com');
  const [password, setPassword] = useState('Workforce2026!');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid email or password. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const setPreset = (presetEmail, presetPwd) => {
    setEmail(presetEmail);
    setPassword(presetPwd);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-900 text-white shadow-lg shadow-navy-900/30">
            <BarChart3 className="h-7 w-7 text-blue-400" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900">
          WorkforceIQ Enterprise
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          AI-Powered Demand Forecasting & Skill Gap Intelligence Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-card rounded-2xl border border-slate-200 sm:px-10">
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 flex items-start gap-2.5 text-xs text-rose-700">
                <ShieldAlert className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <Input
              label="Corporate Email"
              type="email"
              icon={Mail}
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@workforceiq.com"
            />

            <Input
              label="Password"
              type="password"
              icon={Lock}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Remember session</span>
              </label>
              <span className="text-slate-400">Enterprise SSO Active</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full bg-blue-600 hover:bg-blue-700"
              isLoading={isLoading}
            >
              Sign In to Platform
            </Button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 text-center mb-3">
              Developer & Role Test Presets
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPreset('admin@workforceiq.com', 'Workforce2026!')}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />
                <span>Admin Login</span>
              </button>
              <button
                type="button"
                onClick={() => setPreset('hr@workforceiq.com', 'Workforce2026!')}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <span>HR Partner</span>
              </button>
              <button
                type="button"
                onClick={() => setPreset('pm@workforceiq.com', 'Workforce2026!')}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <span>Project Mgr</span>
              </button>
              <button
                type="button"
                onClick={() => setPreset('employee@workforceiq.com', 'Workforce2026!')}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <span>Employee</span>
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          WorkforceIQ Core • Secure Token-Based Authorization & Role Governance
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
