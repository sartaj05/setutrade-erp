import { useEffect, useState } from 'react';
import { getApiResource } from './api';
import { useAuth } from '../context/AuthContext';

export function useApiData(resource, fallback, key) {
  const { mode } = useAuth();
  const [data, setData] = useState(fallback);
  const [source, setSource] = useState('demo');

  useEffect(() => {
    let active = true;
    if (mode !== 'api') {
      setData(fallback); setSource('demo');
      return () => { active = false; };
    }
    getApiResource(resource)
      .then((payload) => {
        if (!active) return;
        setData(key ? payload[key] : payload);
        setSource('api');
      })
      .catch(() => {
        if (!active) return;
        setData(fallback); setSource('fallback');
      });
    return () => { active = false; };
  }, [resource, mode, key]);

  return { data, source };
}
