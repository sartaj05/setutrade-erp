import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';

function useTinyRouter() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (to) => {
    window.history.pushState({}, '', to);
    setPath(to);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return { path, navigate };
}

export default function App() {
  const { path, navigate } = useTinyRouter();
  return <LandingPage navigate={navigate} path={path} />;
}
