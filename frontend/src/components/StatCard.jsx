export default function StatCard({ label, value, hint, tone = 'neutral' }) {
  return (
    <article className={`stat-card ${tone}`}>
      <div className="stat-top"><span>{label}</span><i /></div>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  );
}
