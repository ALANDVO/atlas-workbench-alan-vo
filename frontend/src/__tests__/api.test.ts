import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockGet, mockPost, mockPatch } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPatch: vi.fn(),
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
      post: mockPost,
      patch: mockPatch,
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}));

import { api } from '../api/client';

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getAuthStatus calls /auth/me', async () => {
    mockGet.mockResolvedValue({
      data: { authenticated: true, user: { id: '1', email: 'a@b.com', name: 'A', roles: ['operator'] } },
    });
    const result = await api.getAuthStatus();
    expect(mockGet).toHaveBeenCalledWith('/auth/me');
    expect(result.authenticated).toBe(true);
  });

  it('createSession posts to /compression/sessions', async () => {
    const sessionData = { session_name: 'Test', mode: 'compress' as const, provider: 'openai', model: 'gpt-4' };
    mockPost.mockResolvedValue({ data: { id: 'abc', ...sessionData } });
    const result = await api.createSession(sessionData);
    expect(mockPost).toHaveBeenCalledWith('/compression/sessions', sessionData);
    expect(result.id).toBe('abc');
  });

  it('getStatsSummary calls /compression/stats/summary', async () => {
    const stats = {
      total_sessions: 5,
      total_requests: 20,
      eligible_requests: 15,
      eligibility_rate: 0.75,
      tokens_before: 1000,
      tokens_after: 300,
      tokens_saved: 700,
      overall_savings_ratio: 0.7,
    };
    mockGet.mockResolvedValue({ data: stats });
    const result = await api.getStatsSummary();
    expect(mockGet).toHaveBeenCalledWith('/compression/stats/summary');
    expect(result.total_sessions).toBe(5);
  });
});