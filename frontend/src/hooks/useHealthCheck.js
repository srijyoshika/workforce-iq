/**
 * Custom React Hook for live system health polling and diagnostics.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getHealthStatus } from '../api/health';

const DEFAULT_POLL_INTERVAL = Number(import.meta.env.VITE_HEALTH_POLL_INTERVAL) || 15000;

export function useHealthCheck(options = {}) {
  const { autoPoll = true, pollInterval = DEFAULT_POLL_INTERVAL } = options;

  const [healthData, setHealthData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState(null);
  const [clientLatencyMs, setClientLatencyMs] = useState(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);

  const isMounted = useRef(true);

  const fetchHealth = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setError(null);

    try {
      const { data, latencyMs } = await getHealthStatus();
      if (isMounted.current) {
        setHealthData(data);
        setClientLatencyMs(latencyMs);
        setLastRefreshedAt(new Date());
        setIsLoading(false);
      }
    } catch (err) {
      if (isMounted.current) {
        setIsError(true);
        setError(err);
        setClientLatencyMs(err.latencyMs || null);
        setLastRefreshedAt(new Date());
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    fetchHealth();

    let timer = null;
    if (autoPoll && pollInterval > 0) {
      timer = setInterval(fetchHealth, pollInterval);
    }

    return () => {
      isMounted.current = false;
      if (timer) clearInterval(timer);
    };
  }, [fetchHealth, autoPoll, pollInterval]);

  return {
    healthData,
    isLoading,
    isError,
    error,
    clientLatencyMs,
    lastRefreshedAt,
    refetch: fetchHealth,
  };
}

export default useHealthCheck;

