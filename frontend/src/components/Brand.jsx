export default function Brand({ compact = false }) {
  return (
    <div className="brand" aria-label="SetuStock NCR">
      <div className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      {!compact && (
        <div>
          <strong>SetuStock</strong>
          <small>NCR wholesale OS</small>
        </div>
      )}
    </div>
  );
}
