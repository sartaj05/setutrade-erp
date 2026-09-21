const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status = 0, network = false, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.network = network;
    this.details = details;
  }
}

function authHeaders(extra = {}) {
  const token = localStorage.getItem('setustock_token');
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...extra };
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return response.json();
  return { text: await response.text() };
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('setustock_refresh_token');
  if (!refreshToken) return false;
  try {
    const response = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    localStorage.setItem('setustock_token', data.token);
    return true;
  } catch {
    return false;
  }
}

export async function apiRequest(path, options = {}, retry = true) {
  const isForm = options.body instanceof FormData;
  const headers = authHeaders({ ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) });
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (response.status === 401 && retry && !path.startsWith('/auth/')) {
      const refreshed = await refreshAccessToken();
      if (refreshed) return apiRequest(path, options, false);
    }
    const data = await parseResponse(response);
    if (!response.ok) throw new ApiError(data.detail || data.text || `API request failed (${response.status})`, response.status, false, data);
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Django API is unavailable.', 0, true);
  }
}

export async function loginApi(email, password) {
  const data = await apiRequest('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
  localStorage.setItem('setustock_token', data.token);
  localStorage.setItem('setustock_refresh_token', data.refreshToken || '');
  return data.user;
}

export async function logoutApi() {
  try { await apiRequest('/auth/logout/', { method: 'POST', body: '{}' }); } catch { /* local logout still wins */ }
  localStorage.removeItem('setustock_token');
  localStorage.removeItem('setustock_refresh_token');
}

export function getApiResource(resource, query = '') {
  return apiRequest(`/${resource}/${query ? `?${query}` : ''}`);
}

export function createApiResource(resource, payload) {
  return apiRequest(`/${resource}/`, { method: 'POST', body: JSON.stringify(payload) });
}

export function patchApiResource(path, payload) {
  return apiRequest(`/${path.replace(/^\//, '')}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function postApiAction(path, payload = {}) {
  return apiRequest(`/${path.replace(/^\//, '')}`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function uploadAttachment(module, entityId, file) {
  const form = new FormData();
  form.append('module', module);
  form.append('entityId', entityId);
  form.append('file', file);
  return apiRequest('/attachments/', { method: 'POST', body: form });
}

export async function importCsv(resource, file) {
  const form = new FormData();
  form.append('file', file);
  return apiRequest(`/import/${resource}/`, { method: 'POST', body: form });
}

export function exportUrl(resource) {
  return `${API_BASE}/export/${resource}/`;
}

export const apiBase = API_BASE;

export async function downloadCsv(resource) {
  const token = localStorage.getItem('setustock_token');
  const response = await fetch(`${API_BASE}/export/${resource}/`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok) throw new ApiError(`Export failed (${response.status})`, response.status);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `setustock-${resource}.csv`;
  document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url);
}

export function requestPasswordReset(email) {
  return apiRequest('/auth/password-reset/request/', { method: 'POST', body: JSON.stringify({ email }) });
}

export function confirmPasswordReset(uid, token, newPassword) {
  return apiRequest('/auth/password-reset/confirm/', { method: 'POST', body: JSON.stringify({ uid, token, newPassword }) });
}
