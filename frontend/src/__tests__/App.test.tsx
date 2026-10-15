import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock the API module so component tests don't hit a real backend
vi.mock('../api/client', () => ({
  api: {
    getAuthStatus: vi.fn(),
    getCsrfToken: vi.fn(),
    getLoginUrl: () => '/auth/login',
    getStatsSummary: vi.fn(),
    listSessions: vi.fn(),
    createSession: vi.fn(),
    logout: vi.fn(),
    setCsrfToken: vi.fn(),
    clearCsrfToken: vi.fn(),
  },
}));

// Mock react-router-dom to avoid jsdom history warnings
vi.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Routes: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Route: ({ element }: { element?: React.ReactNode }) => element ?? null,
  Navigate: () => null,
  Link: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock useAuth to control auth state directly
vi.mock('../hooks/useAuth', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: vi.fn(),
}));

import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';

const mockApi = vi.mocked(api);
const mockUseAuth = vi.mocked(useAuth);

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getStatsSummary.mockResolvedValue({
      total_sessions: 3,
      total_requests: 10,
      eligible_requests: 8,
      eligibility_rate: 0.8,
      tokens_before: 1000,
      tokens_after: 300,
      tokens_saved: 700,
      overall_savings_ratio: 0.7,
    });
    mockApi.listSessions.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 });
  });

  it('renders dashboard when authenticated', async () => {
    mockUseAuth.mockReturnValue({
      authStatus: { authenticated: true, user: { id: '1', email: 't@t.com', name: 'Test', roles: ['operator'] } },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    });

    render(<App />);
    const elements = await screen.findAllByText('3');
    expect(elements.length).toBeGreaterThan(0);
  });

  it('shows login page when unauthenticated', async () => {
    mockUseAuth.mockReturnValue({
      authStatus: { authenticated: false },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    });

    render(<App />);
    const elements = await screen.findAllByText('Sign in with SSO');
    expect(elements.length).toBeGreaterThan(0);
  });
});