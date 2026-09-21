import { useAuth } from '../context/AuthContext';
import { roleHomeCopy } from '../data/demoData';

export default function DashboardPage() {
  const { user } = useAuth();
  return (
    <div className="empty-dashboard">
      <span className="section-kicker">{user.role} workspace</span>
      <h1>Good afternoon, {user.name.split(' ')[0]}.</h1>
      <p>{roleHomeCopy[user.role]}</p>
      <div className="placeholder-panel">Operational widgets load here in the next feature commit.</div>
    </div>
  );
}
