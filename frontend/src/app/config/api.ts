export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // Include HTTP-only session cookies
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody?.error?.message || response.statusText || 'Request failed';
    throw new Error(message);
  }

  return response.json();
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  return fetchApi<T>(endpoint, { method: 'GET' });
}

export async function apiPost<T>(endpoint: string, body?: any): Promise<T> {
  return fetchApi<T>(endpoint, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}
