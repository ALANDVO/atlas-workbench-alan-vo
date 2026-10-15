import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { api } from '../api/client';
import type { AuthStatus } from '../types';

interface AuthContextType {
  authStatus: AuthStatus | null;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshAuth = useCallback(async () => {
    try {
      const status = await api.getAuthStatus();
      setAuthStatus(status);
      if (status.authenticated) {
        await api.getCsrfToken();
      }
    } catch (error) {
      console.error('Auth refresh failed:', error);
      setAuthStatus({ authenticated: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAuth();

    const handleUnauthorized = () => {
      setAuthStatus({ authenticated: false });
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [refreshAuth]);

  const login = useCallback(() => {
    window.location.href = api.getLoginUrl();
  }, []);

  const logout = useCallback(async () => {
    try {
      const { logout_url } = await api.logout();
      window.location.href = logout_url;
    } catch (error) {
      console.error('Logout failed:', error);
      window.location.href = '/';
    }
  }, []);

  return (
    <AuthContext.Provider value={{ authStatus, loading, login, logout, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}