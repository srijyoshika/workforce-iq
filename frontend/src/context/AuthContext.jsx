import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('workforce_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('workforce_token'));
  const [isLoading, setIsLoading] = useState(true);

  // Validate or restore user profile on mount if token exists
  useEffect(() => {
    let isMounted = true;
    async function restoreSession() {
      const storedToken = localStorage.getItem('workforce_token');
      if (!storedToken) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const profile = await authApi.getCurrentUser();
        if (isMounted) {
          setUser(profile);
          localStorage.setItem('workforce_user', JSON.stringify(profile));
        }
      } catch (err) {
        console.warn('Session expired or invalid:', err.message);
        if (isMounted) {
          setUser(null);
          setToken(null);
          localStorage.removeItem('workforce_token');
          localStorage.removeItem('workforce_user');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    setToken(data.access_token);
    localStorage.setItem('workforce_token', data.access_token);

    const profile = {
      id: data.user_id,
      email: data.email,
      system_role: data.role,
      first_name: data.first_name,
      last_name: data.last_name,
    };
    setUser(profile);
    localStorage.setItem('workforce_user', JSON.stringify(profile));
    return profile;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('workforce_token');
      localStorage.removeItem('workforce_user');
    }
  }, []);

  const hasRole = useCallback(
    (...allowedRoles) => {
      if (!user || !user.system_role) return false;
      const userRole = String(user.system_role).toUpperCase();
      return allowedRoles.some((r) => String(r).toUpperCase() === userRole);
    },
    [user]
  );

  const value = {
    user,
    token,
    isAuthenticated: Boolean(token && user),
    isLoading,
    login,
    logout,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
