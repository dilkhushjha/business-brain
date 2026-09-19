// Shared API access for the dashboard.
// The browser receives only the public API base URL and the local access
// token for the selected business. Server secrets must never be placed in
// NEXT_PUBLIC_* variables.

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : ""
);
const DEFAULT_BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || (
  process.env.NODE_ENV === "development" ? "11111111-1111-1111-1111-111111111111" : ""
);

const BUSINESS_ID_KEY = "bb_business_id";
const TOKEN_KEY_PREFIX = "bb_api_token:";

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try { return window.localStorage.getItem(key); } catch { return null; }
}

function writeStorage(key: string, value: string) {
  if (typeof window === "undefined") return;
  try { window.localStorage.setItem(key, value); } catch { /* non-fatal */ }
}

export function getBusinessId(): string {
  return readStorage(BUSINESS_ID_KEY) || DEFAULT_BUSINESS_ID;
}

export function setBusinessId(id: string) { writeStorage(BUSINESS_ID_KEY, id); }

export function getToken(businessId: string = getBusinessId()): string | null {
  return readStorage(`${TOKEN_KEY_PREFIX}${businessId}`);
}

export function setToken(businessId: string, token: string) {
  writeStorage(`${TOKEN_KEY_PREFIX}${businessId}`, token);
}

export function clearToken(businessId: string = getBusinessId()) {
  if (typeof window === "undefined") return;
  try { window.localStorage.removeItem(`${TOKEN_KEY_PREFIX}${businessId}`); } catch { /* ignore */ }
}

export function hasToken(): boolean { return Boolean(getToken()); }

export class ApiAuthError extends Error {}

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

export async function registerAndConnect(businessId: string, registrationKey?: string): Promise<string> {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  const headers: Record<string, string> = {};
  if (registrationKey) headers["X-Connector-Registration-Key"] = registrationKey;
  const response = await fetch(`${API_BASE_URL}/connectors/register/${businessId}`, { method: "POST", headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Registration failed (${response.status})`);
  if (!data.token) throw new Error("Registration response did not include a token.");
  setBusinessId(businessId);
  setToken(businessId, data.token);
  return data.token as string;
}
