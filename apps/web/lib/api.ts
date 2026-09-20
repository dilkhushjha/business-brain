// Shared authenticated API access for the dashboard.
// Human users authenticate with a username/email/phone + password.
// Connector credentials never enter the browser dashboard flow.

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : ""
);

const TOKEN_KEY = "bb_user_session";
const BUSINESS_KEY = "bb_business_context";

export type SessionUser = {
  id: string;
  username: string;
  email: string | null;
  phone: string | null;
  business: {
    id: string;
    name: string;
    industry: string;
    role: string;
  };
};

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try { return window.sessionStorage.getItem(key); } catch { return null; }
}

function writeStorage(key: string, value: string) {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.setItem(key, value); } catch { /* non-fatal */ }
}

function removeStorage(key: string) {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.removeItem(key); } catch { /* non-fatal */ }
}

export function getToken(): string | null {
  return readStorage(TOKEN_KEY);
}

export function setSession(token: string, user: SessionUser) {
  writeStorage(TOKEN_KEY, token);
  writeStorage(BUSINESS_KEY, user.business.id);
}

export function getBusinessId(): string {
  return readStorage(BUSINESS_KEY) || "";
}

export function hasToken(): boolean {
  return Boolean(getToken());
}

export function clearSession() {
  removeStorage(TOKEN_KEY);
  removeStorage(BUSINESS_KEY);
}

export class ApiAuthError extends Error {}

async function authRequest(path: string, body: unknown) {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Authentication failed (${response.status})`);
  if (!data.access_token || !data.user) throw new Error("Authentication response was incomplete.");
  setSession(data.access_token, data.user);
  return data as { access_token: string; token_type: string; user: SessionUser };
}

export function login(identifier: string, password: string) {
  return authRequest("/auth/login", { identifier, password });
}

export function register(payload: {
  username: string;
  email?: string;
  phone?: string;
  password: string;
  business_name: string;
  industry: string;
}) {
  return authRequest("/auth/register", payload);
}

export async function getCurrentUser(): Promise<SessionUser> {
  const response = await apiFetch("/auth/me");
  if (!response.ok) throw new ApiAuthError(`Authentication required (${response.status})`);
  const user = await response.json() as SessionUser;
  setSession(getToken() || "", user);
  return user;
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401 || response.status === 403) {
    throw new ApiAuthError(`Authentication required (${response.status})`);
  }
  return response;
}
