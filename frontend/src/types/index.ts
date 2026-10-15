export type CompressionMode = 'compress' | 'summarize' | 'off';

export type UserRole = 'operator' | 'analyst' | 'admin';

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  roles: UserRole[];
}

export interface AuthStatus {
  authenticated: boolean;
  user?: UserInfo;
}

export interface CompressionSession {
  id: string;
  session_name: string;
  mode: CompressionMode;
  provider: string;
  model: string;
  base_url?: string;
  total_requests: number;
  eligible_requests: number;
  tokens_before: number;
  tokens_after: number;
  tokens_saved: number;
  savings_ratio: number;
  created_at: string;
  updated_at: string;
  ended_at?: string;
}

export interface CompressionRequest {
  id: string;
  session_id: string;
  provider: string;
  model: string;
  mode: CompressionMode;
  input_tokens: number;
  output_tokens: number;
  compressed_tokens: number;
  recovered_tokens: number;
  savings: number;
  mcp_recovery_used: boolean;
  duration_ms: number;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SessionCreate {
  session_name: string;
  mode: CompressionMode;
  provider: string;
  model: string;
  base_url?: string;
}

export interface SessionUpdate {
  session_name?: string;
  mode?: CompressionMode;
}

export interface StatsSummary {
  total_sessions: number;
  total_requests: number;
  eligible_requests: number;
  eligibility_rate: number;
  tokens_before: number;
  tokens_after: number;
  tokens_saved: number;
  overall_savings_ratio: number;
}