const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export const API_BASE_URL = String(rawBaseUrl).replace(/\/+$/, '')

export function apiUrl(path = '') {
  if (!path) return API_BASE_URL
  if (!API_BASE_URL) return path
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

