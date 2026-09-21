const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status = 0, network = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.network = network;
  }
}

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('setustock_token');
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    let data = {};
    try { data = await response.json(); } catch { data = {}; }
    if (!response.ok) throw new ApiError(data.detail || `API request failed (${response.status})`, response.status, false);
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Django API is unavailable.', 0, true);
  }
}

export async function loginApi(email, password) {
  const data = await apiRequest('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
  localStorage.setItem('setustock_token', data.token);
  return data.user;
}

export function getApiResource(resource) {
  return apiRequest(`/${resource}/`);
}
