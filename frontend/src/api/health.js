/**
 * Health & Infrastructure API Services.
 */

import apiClient from './client';

/**
 * Fetch detailed system and database health diagnostics.
 * @returns {Promise<{data: import('./types').HealthResponse, latencyMs: number}>}
 */
export async function getHealthStatus() {
  const response = await apiClient.get('/health');
  return {
    data: response.data,
    latencyMs: response.latencyMs,
  };
}

/**
 * Check basic container liveness.
 */
export async function checkLiveness() {
  const response = await apiClient.get('/health/live');
  return response.data;
}

/**
 * Check subsystem readiness.
 */
export async function checkReadiness() {
  const response = await apiClient.get('/health/ready');
  return response.data;
}

