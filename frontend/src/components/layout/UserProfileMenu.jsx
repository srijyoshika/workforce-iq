import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, User, Shield, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Badge from '../ui/Badge';

export function UserProfileMenu() {
  const { user, logout, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

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

  if (!isAuthenticated || !user) {
    return (
      <button
        type="button"
        onClick={() => navigate('/login')}
        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
      >
        Sign In
      </button>
    );
  }

  const initials = `${user.first_name?.[0] || 'U'}${user.last_name?.[0] || 'A'}`;

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-100 transition-colors focus:outline-none"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy-900 text-white font-mono text-xs font-bold shadow-sm">
          {initials}
        </div>
        <div className="hidden sm:flex flex-col text-left">
          <span className="text-xs font-bold text-slate-800 leading-none">
            {user.first_name} {user.last_name}
          </span>
          <span className="text-[10px] text-slate-400 capitalize mt-0.5">
            {user.system_role?.replace('_', ' ')?.toLowerCase() || 'Employee'}
          </span>
        </div>
        <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white shadow-xl z-50 overflow-hidden divide-y divide-slate-100 animate-in fade-in duration-100">
          <div className="p-4 bg-slate-50/60">
            <p className="text-xs font-bold text-slate-900">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-[11px] text-slate-500 font-mono truncate">{user.email}</p>
            <div className="mt-2 flex items-center gap-1.5">
              <Badge variant="navy" size="sm">
                {user.system_role || 'EMPLOYEE'}
              </Badge>
              {user.department && (
                <span className="text-[10px] text-slate-400">{user.department}</span>
              )}
            </div>
          </div>

          <div className="p-1">
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate(`/employees/${user.id}`);
              }}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-700 hover:bg-slate-100 transition-colors text-left"
            >
              <User className="h-4 w-4 text-slate-400" />
              <span>View My Profile</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate('/admin');
              }}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-700 hover:bg-slate-100 transition-colors text-left"
            >
              <Shield className="h-4 w-4 text-slate-400" />
              <span>System Administration</span>
            </button>
          </div>

          <div className="p-1">
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors text-left"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserProfileMenu;
