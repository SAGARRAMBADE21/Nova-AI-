/**
 * Central API client for Nova AI / QueryMind frontend.
 * All calls go through here so auth headers are automatically attached.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('nova_token');
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string> ?? {}) },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────

export interface OnboardPayload {
  company_name: string;
  admin_email: string;
  admin_password: string;
}
export interface OnboardResponse {
  company_name: string;
  tenant_id: string;
  join_code: string;
  message: string;
}

export function onboard(data: OnboardPayload) {
  return request<OnboardResponse>('/onboard', { method: 'POST', body: data });
}

// ─────────────────────────────────────────────────────────────────────────

export interface JoinPayload {
  join_code: string;
  email: string;
  password: string;
}
export interface JoinResponse {
  token: string;
  company_name: string;
  role: string;
  message: string;
}

export function joinWorkspace(data: JoinPayload) {
  return request<JoinResponse>('/join', { method: 'POST', body: data });
}

// ─────────────────────────────────────────────────────────────────────────

export interface RegisterPayload {
  join_code: string;
  email: string;
  password: string;
}
export interface RegisterResponse {
  message: string;
  role: string;
}

export function register(data: RegisterPayload) {
  return request<RegisterResponse>('/register', { method: 'POST', body: data });
}

// ── Chat ─────────────────────────────────────────────────────────────────

export interface ChatPayload {
  prompt: string;
  session_id?: string;
}
export interface ChatResponse {
  response: string;
  session_id?: string;
  tenant_id: string;
  role: string;
}

export function sendChat(data: ChatPayload) {
  return request<ChatResponse>('/chat', { method: 'POST', body: data });
}

// ── Admin ─────────────────────────────────────────────────────────────────

export interface InviteUserPayload {
  email: string;
  role: string;
}
export function inviteUser(data: InviteUserPayload) {
  return request<{ message: string; invite_email: string }>('/invite-user', { method: 'POST', body: data });
}

export function listUsers() {
  return request<{ tenant_id: string; users: Record<string, unknown>[] }>('/users');
}

export function getMetrics() {
  return request<Record<string, unknown>>('/metrics');
}

// ── Email Config ──────────────────────────────────────────────────────────

export interface EmailConfigPayload {
  sender_email: string;
  sender_password: string;
}
export function setEmailConfig(data: EmailConfigPayload) {
  return request<{ message: string; sender: string }>('/email-config', { method: 'POST', body: data });
}

// ── Health ────────────────────────────────────────────────────────────────

export function healthCheck() {
  return request<{ status: string; version: string }>('/health');
}
