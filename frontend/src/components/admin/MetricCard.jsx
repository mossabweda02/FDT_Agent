// ─── MetricCard.jsx ───────────────────────────────────────────────────────────
// Carte KPI réutilisable.
// Props :
//   label       string   — libellé affiché
//   value       string   — valeur principale (déjà formatée)
//   delta       string|null — variation (ex: "+12%"), null = pas de delta
//   deltaUp     bool|null   — true = vert, false = rouge
//   accentColor string   — couleur du point indicateur gauche

const MetricCard = ({ label, value, delta, deltaUp, accentColor }) => {
  return (
    <div style={{
      background: '#ffffff',
      borderRadius: 12,
      border: '1px solid #E5E7EB',
      padding: '20px 22px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
      transition: 'box-shadow 0.15s',
    }}
    onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'}
    onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.04)'}
    >
      {/* Label + dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: accentColor,
          flexShrink: 0,
        }} />
        <span style={{
          fontSize: 12,
          color: '#6B7280',
          fontWeight: 500,
          letterSpacing: '0.02em',
          userSelect: 'none',
        }}>
          {label}
        </span>
      </div>

      {/* Valeur principale */}
      <div style={{
        fontSize: 26,
        fontWeight: 700,
        color: '#111827',
        letterSpacing: '-0.5px',
        lineHeight: 1,
      }}>
        {value}
      </div>

      {/* Delta (optionnel) */}
      {delta !== null && delta !== undefined && (
        <div style={{
          fontSize: 12,
          fontWeight: 500,
          color: deltaUp ? '#059669' : '#DC2626',
          display: 'flex',
          alignItems: 'center',
          gap: 3,
        }}>
          <span>{deltaUp ? '↑' : '↓'}</span>
          <span>{delta}</span>
          <span style={{ color: '#9CA3AF', fontWeight: 400, marginLeft: 2 }}>vs 30j</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;