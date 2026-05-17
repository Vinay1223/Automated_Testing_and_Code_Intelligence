/** Server-side helper to call the CodeIntel API with the current user's JWT. */
import { auth } from '@clerk/nextjs/server';

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { getToken } = auth();
  const token = await getToken({ template: 'codeintel' });
  const headers = new Headers(init.headers);
  headers.set('content-type', 'application/json');
  if (token) {
    headers.set('authorization', `Bearer ${token}`);
  }
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  const r = await fetch(`${baseUrl}${path}`, { ...init, headers, cache: 'no-store' });
  if (!r.ok) {
    throw new Error(`API ${r.status} ${path}: ${await r.text()}`);
  }
  return (await r.json()) as T;
}
