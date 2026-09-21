import { useEffect, useState } from 'react';
import { getApiResource } from './api';
import { useAuth } from '../context/AuthContext';

export function useApiData(resource, fallback, key) {
  const { mode } = useAuth();
  const [data, setData] = useState(fallback);
  const [source, setSource] = useState(mode === 'api' ? 'loading' : 'demo');
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    if (mode !== 'api') {
      setData(fallback); setSource('demo'); setError('');
      return () => { active = false; };
    }
    setSource('loading'); setError('');
    getApiResource(resource)
      .then((payload) => {
        if (!active) return;
        setData(key ? payload[key] : payload);
        setSource('api');
      })
      .catch((err) => {
        if (!active) return;
        setSource('error');
        setError(err.message || 'Could not load live data.');
      });
    return () => { active = false; };
  }, [resource, mode, key, version]);

  return { data, source, error, refresh: () => setVersion((v) => v + 1) };
}
