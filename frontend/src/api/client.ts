/**
 * - Desarrollo: Vite reenvía `/api/*` al FastAPI (`vite.config.ts`).
 * - Docker (Nginx): mismo origen; Nginx proxea `/api/` → servicio `api`.
 * - Build suelto: opcional `VITE_API_URL` (URL absoluta del API, sin barra final).
 */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const explicit = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
  if (explicit) {
    return `${explicit.replace(/\/$/, "")}${p}`;
  }
  return `/api${p}`;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const baseHeaders: Record<string, string> = { Accept: "application/json" };
  const extra = init?.headers as Record<string, string> | undefined;
  const headers = { ...baseHeaders, ...extra };

  const res = await fetch(apiUrl(path), {
    ...init,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  return fetchJson<TResponse>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
