/**
 * WorkforceIQ Enterprise API Client.
 * Configured Axios instance with request/response timing, automatic Bearer JWT injection,
 * and normalized error handling.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor: attach auth token and start timing
apiClient.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: performance.now() };
    const token = localStorage.getItem('workforce_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: record latency and format errors
apiClient.interceptors.response.use(
  (response) => {
    const duration = performance.now() - (response.config.metadata?.startTime || performance.now());
    response.latencyMs = Math.round(duration);
    return response;
  },
  (error) => {
    if (error.config?.metadata) {
      error.latencyMs = Math.round(performance.now() - error.config.metadata.startTime);
    }

    // Auto-logout on 401 Unauthorized if token expired
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      if (currentPath !== '/login') {
        localStorage.removeItem('workforce_token');
        localStorage.removeItem('workforce_user');
      }
    }

    // Normalize error payload
    let errorDetail = 'An unexpected error occurred';
    if (error.response?.data?.detail) {
      if (typeof error.response.data.detail === 'string') {
        errorDetail = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        errorDetail = error.response.data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      }
    } else if (error.message) {
      errorDetail = error.message;
    }

    const normalizedError = {
      message: errorDetail,
      status: error.response?.status || 0,
      data: error.response?.data,
      latencyMs: error.latencyMs,
    };
    return Promise.reject(normalizedError);
  }
);

export default apiClient;
