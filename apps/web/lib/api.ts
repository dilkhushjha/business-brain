// Shared API access for the dashboard.
//
// V1 has no separate user/login system (see docs/architecture/security.md):
// the token issued by POST /connectors/register/{business_id} doubles as
// both the automated connector's upload credential and this dashboard's
// general API access token. This module is the one place that knows how
// to store/attach it, so every component just calls apiFetch() instead of
// raw fetch().

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const DEFAULT_BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "11111111-1111-1111-1111-111111111111";

const BUSINESS_ID_KEY = "bb_business_id";
const TOKEN_KEY_PREFIX = "bb_api_token:";

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // localStorage can throw in private-browsing modes -- non-fatal, the
    // token just won't persist across reloads.
  }
}

export function getBusinessId(): string {
  return readStorage(BUSINESS_ID_KEY) || DEFAULT_BUSINESS_ID;
}

export function setBusinessId(id: string) {
  writeStorage(BUSINESS_ID_KEY, id);
}

export function getToken(businessId: string = getBusinessId()): string | null {
  return readStorage(`${TOKEN_KEY_PREFIX}${businessId}`);
}

export function setToken(businessId: string, token: string) {
  writeStorage(`${TOKEN_KEY_PREFIX}${businessId}`, token);
}

export function clearToken(businessId: string = getBusinessId()) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(`${TOKEN_KEY_PREFIX}${businessId}`);
  } catch {
    // ignore
  }
}

export function hasToken(): boolean {
  return Boolean(getToken());
}

/** Thrown when the API responds 401/403 -- distinct from a network error or
 * the backend simply being unreachable, so callers can prompt to
 * (re-)connect instead of silently falling back to demo data forever. */
export class ApiAuthError extends Error {}

/** Fetch a path under API_BASE_URL with the stored bearer token attached.
 * Throws ApiAuthError on 401/403 rather than returning the response, so
 * callers can't accidentally treat "unauthorized" the same as "no data". */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401 || response.status === 403) {
    throw new ApiAuthError(`Authentication required (${response.status})`);
  }
  return response;
}

/** Exchange a registration key for an API token (POST
 * /connectors/register/{business_id}) and store both the business ID and
 * the resulting token for apiFetch() to use. This is the one call in this
 * file that intentionally does NOT go through apiFetch -- there's no token
 * to attach yet, that's the whole point. */
export async function registerAndConnect(businessId: string, registrationKey?: string): Promise<string> {
  const headers: Record<string, string> = {};
  if (registrationKey) headers["X-Connector-Registration-Key"] = registrationKey;
  const response = await fetch(`${API_BASE_URL}/connectors/register/${businessId}`, {
    method: "POST",
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Registration failed (${response.status})`);
  }
  if (!data.token) {
    throw new Error("Registration response did not include a token.");
  }
  setBusinessId(businessId);
  setToken(businessId, data.token);
  return data.token as string;
}
