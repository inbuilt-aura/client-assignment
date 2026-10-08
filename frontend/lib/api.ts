export type LocationOption = { id: string; label: string; latitude: number; longitude: number };
export type RadiusCoverage = { mode: "RADIUS"; location: LocationOption; radius_km: number };
export type AreasCoverage = { mode: "AREAS"; area_ids: string[] };
export type Coverage = RadiusCoverage | AreasCoverage;
export type CoverageRecord = { vendor_id: string; revision: number; coverage: Coverage | null; updated_at: string | null };

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/v1";
const TOKEN_KEY = "nova_access_token";

export type SignedInUser = { id: string; email: string; organization_id: string };

export function saveAccessToken(token: string) {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken() {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window === "undefined" ? null : window.sessionStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
    cache: "no-store",
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(payload?.detail?.message ?? payload?.detail?.code ?? "Request failed") as Error & { status: number };
    error.status = response.status;
    throw error;
  }
  return payload as T;
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string; token_type: string; expires_in: number }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  currentUser: () => request<SignedInUser>("/auth/me"),
  getCoverage: (vendorId: string) => request<CoverageRecord>(`/vendors/${vendorId}/service-area`),
  saveCoverage: (vendorId: string, expectedRevision: number, coverage: Coverage) =>
    request<CoverageRecord>(`/vendors/${vendorId}/service-area`, { method: "PATCH", body: JSON.stringify({ expected_revision: expectedRevision, coverage }) }),
  searchLocations: (query: string) => request<LocationOption[]>(`/locations/search?q=${encodeURIComponent(query)}`),
};
