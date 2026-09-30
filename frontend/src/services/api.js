const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
const ACCESS_TOKEN_KEY = 'setustock_token';
const REFRESH_TOKEN_KEY = 'setustock_refresh_token';

export class ApiError extends Error {
  constructor(message, status = 0, network = false, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.network = network;
    this.details = details;
  }
}

function readStorage(storage, key) {
  try { return storage.getItem(key) || ''; } catch { return ''; }
}

export function getAccessToken() {
  return readStorage(sessionStorage, ACCESS_TOKEN_KEY) || readStorage(localStorage, ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return readStorage(sessionStorage, REFRESH_TOKEN_KEY) || readStorage(localStorage, REFRESH_TOKEN_KEY);
}

export function storeAuthTokens(data, remember = false) {
  const target = remember ? localStorage : sessionStorage;
  [localStorage, sessionStorage].forEach((storage) => {
    try {
      storage.removeItem(ACCESS_TOKEN_KEY);
      storage.removeItem(REFRESH_TOKEN_KEY);
    } catch { /* storage may be unavailable in a restricted browser */ }
  });
  target.setItem(ACCESS_TOKEN_KEY, data.token || '');
  target.setItem(REFRESH_TOKEN_KEY, data.refreshToken || '');
}

export function storeAccessToken(token) {
  const target = readStorage(sessionStorage, REFRESH_TOKEN_KEY) ? sessionStorage : localStorage;
  target.setItem(ACCESS_TOKEN_KEY, token || '');
}

export function clearAuthTokens() {
  [localStorage, sessionStorage].forEach((storage) => {
    try {
      storage.removeItem(ACCESS_TOKEN_KEY);
      storage.removeItem(REFRESH_TOKEN_KEY);
    } catch { /* storage may be unavailable in a restricted browser */ }
  });
}

function authHeaders(extra = {}) {
  const token = getAccessToken();
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...extra };
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return response.json();
  return { text: await response.text() };
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const response = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    storeAccessToken(data.token);
    return true;
  } catch {
    return false;
  }
}

export async function apiRequest(path, options = {}, retry = true) {
  const isForm = options.body instanceof FormData;
  const headers = authHeaders({ ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) });
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), Number(import.meta.env.VITE_API_TIMEOUT_MS || 12000));
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal });
    if (response.status === 401 && retry && !path.startsWith('/auth/')) {
      const refreshed = await refreshAccessToken();
      if (refreshed) return apiRequest(path, options, false);
    }
    const data = await parseResponse(response);
    if (!response.ok) throw new ApiError(data.detail || data.text || `API request failed (${response.status})`, response.status, false, data);
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(error?.name === 'AbortError' ? 'Django API request timed out.' : 'Django API is unavailable.', 0, true);
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function loginApi(email, password, { remember = false } = {}) {
  const data = await apiRequest('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
  storeAuthTokens(data, remember);
  return data.user;
}

export async function registerApi(details, { remember = false } = {}) {
  const data = await apiRequest('/auth/register/', { method: 'POST', body: JSON.stringify(details) });
  storeAuthTokens(data, remember);
  return data.user;
}

export async function logoutApi() {
  try { await apiRequest('/auth/logout/', { method: 'POST', body: '{}' }); } catch { /* local logout still wins */ }
  clearAuthTokens();
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

export async function previewImport(resource, file, mapping = {}) {
  const form = new FormData();
  form.append('resource', resource);
  form.append('mapping', JSON.stringify(mapping));
  form.append('file', file);
  return apiRequest('/imports/preview/', { method: 'POST', body: form });
}

export function commitImport(batchId) {
  return postApiAction(`imports/${batchId}/commit/`);
}

export function rollbackImport(batchId) {
  return postApiAction(`imports/${batchId}/rollback/`);
}

export function submitOnboardingFeedback(payload) {
  return createApiResource('onboarding/feedback', payload);
}

export function exportUrl(resource) {
  return `${API_BASE}/export/${resource}/`;
}

export const apiBase = API_BASE;

export function healthApi() {
  return apiRequest('/health/');
}

export async function downloadCsv(resource) {
  const token = getAccessToken();
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
