import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

function TestConsumer() {
  const { user, isAuthenticated, hasRole, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? 'LOGGED_IN' : 'LOGGED_OUT'}</span>
      <span data-testid="user-email">{user?.email || 'NONE'}</span>
      <span data-testid="is-admin">{hasRole('ADMIN') ? 'YES' : 'NO'}</span>
      <button
        onClick={() =>
          login('director@workforceiq.com', 'password123')
        }
      >
        Trigger Login
      </button>
      <button onClick={logout}>Trigger Logout</button>
    </div>
  );
}

describe('AuthContext and RBAC System', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes in logged-out state when no token in localStorage', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_OUT');
    expect(screen.getByTestId('user-email').textContent).toBe('NONE');
    expect(screen.getByTestId('is-admin').textContent).toBe('NO');
  });

  it('updates state and localStorage on login', async () => {
    authApi.login.mockResolvedValueOnce({
      access_token: 'fake-jwt-token-2026',
      user_id: 'emp-1',
      email: 'director@workforceiq.com',
      role: 'ADMIN',
      first_name: 'Sarah',
      last_name: 'Connor',
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText('Trigger Login').click();
    });

    expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_IN');
    expect(screen.getByTestId('user-email').textContent).toBe('director@workforceiq.com');
    expect(screen.getByTestId('is-admin').textContent).toBe('YES');
    expect(localStorage.getItem('workforce_token')).toBe('fake-jwt-token-2026');
  });

  it('clears state and localStorage on logout', async () => {
    authApi.login.mockResolvedValueOnce({
      access_token: 'fake-jwt-token-2026',
      user_id: 'emp-1',
      email: 'director@workforceiq.com',
      role: 'ADMIN',
      first_name: 'Sarah',
      last_name: 'Connor',
    });
    authApi.logout.mockResolvedValueOnce({});

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText('Trigger Login').click();
    });
    expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_IN');

    await act(async () => {
      screen.getByText('Trigger Logout').click();
    });

    expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_OUT');
    expect(localStorage.getItem('workforce_token')).toBeNull();
  });
});
