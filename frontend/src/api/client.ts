import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { AuthStatus, CompressionSession, CompressionRequest, PaginatedResponse, SessionCreate, SessionUpdate, StatsSummary } from '../types';

const API_BASE = '';

class ApiClient {
  private client: AxiosInstance;
  private csrfToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method || '')) {
        config.headers['X-CSRF-Token'] = this.csrfToken;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Clear auth state on 401
          this.csrfToken = null;
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
        return Promise.reject(error);
      }
    );
  }

  setCsrfToken(token: string) {
    this.csrfToken = token;
  }

  clearCsrfToken() {
    this.csrfToken = null;
  }

  // Auth
  async getAuthStatus(): Promise<AuthStatus> {
    const response = await this.client.get<AuthStatus>('/auth/me');
    return response.data;
  }

  async getCsrfToken(): Promise<string> {
    const response = await this.client.get<{ csrf_token: string }>('/auth/csrf');
    this.csrfToken = response.data.csrf_token;
    return this.csrfToken;
  }

  async verifyCsrf(token: string): Promise<boolean> {
    const response = await this.client.post<{ valid: boolean }>('/auth/verify-csrf', {}, {
      headers: { 'X-CSRF-Token': token },
    });
    return response.data.valid;
  }

  async logout(): Promise<{ logout_url: string }> {
    const response = await this.client.post<{ logout_url: string }>('/auth/logout');
    this.clearCsrfToken();
    return response.data;
  }

  getLoginUrl(): string {
    return `${API_BASE}/auth/login`;
  }

  // Compression Sessions
  async createSession(data: SessionCreate): Promise<CompressionSession> {
    const response = await this.client.post<CompressionSession>('/compression/sessions', data);
    return response.data;
  }

  async listSessions(params?: {
    page?: number;
    page_size?: number;
    mode?: string;
  }): Promise<PaginatedResponse<CompressionSession>> {
    const response = await this.client.get<PaginatedResponse<CompressionSession>>('/compression/sessions', { params });
    return response.data;
  }

  async getSession(id: string): Promise<CompressionSession> {
    const response = await this.client.get<CompressionSession>(`/compression/sessions/${id}`);
    return response.data;
  }

  async updateSession(id: string, data: SessionUpdate): Promise<CompressionSession> {
    const response = await this.client.patch<CompressionSession>(`/compression/sessions/${id}`, data);
    return response.data;
  }

  async endSession(id: string): Promise<CompressionSession> {
    const response = await this.client.post<CompressionSession>(`/compression/sessions/${id}/end`);
    return response.data;
  }

  async listSessionRequests(
    sessionId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<CompressionRequest>> {
    const response = await this.client.get<PaginatedResponse<CompressionRequest>>(
      `/compression/sessions/${sessionId}/requests`,
      { params }
    );
    return response.data;
  }

  async getStatsSummary(): Promise<StatsSummary> {
    const response = await this.client.get<StatsSummary>('/compression/stats/summary');
    return response.data;
  }

  // Health
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiClient();