// ─── AuditTrailTable.jsx ──────────────────────────────────────────────────────
// Tableau Audit Trail anonymisé.
// Colonnes : Heure · Catégorie · Aperçu · Statut · Latence · Tokens · Tools
//
// Règles confidentialité (Phase 1) :
//   ✅ Affiché  : aperçu tronqué, catégorie, statut, latence, tokens, count tools
//   ❌ Jamais   : question brute, SQL, réponse brute, output tools
//
// Props :
//   events  array  — tableau auditEvents depuis adminMockData.js

// ─── Config statuts ──────────────────────────────────────────────────────────
const STATUS = {
  success: { label: 'Succès',  bg: '#D1FAE5', color: '#065F46', dot: '#10B981' },
  error:   { label: 'Erreur',  bg: '#FEE2E2', color: '#991B1B', dot: '#EF4444' },
  partial: { label: 'Partiel', bg: '#FEF3C7', color: '#92400E', dot: '#F59E0B' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const formatLatency = (ms) => {
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)} min`;
  if (ms >= 1000)  return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
};

const formatTokens = (n) => {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
};

// Couleur latence : rouge si > 20s (critique selon image de référence)
const latencyColor = (ms) => ms > 20000 ? '#EF4444' : ms > 5000 ? '#F59E0B' : '#374151';

// ─── Composant ────────────────────────────────────────────────────────────────
const AuditTrailTable = ({ events }) => {

  // Styles partagés
  const th = {
    padding: '10px 14px',
    fontSize: 11,
    fontWeight: 600,
    color: '#9CA3AF',
    textAlign: 'left',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    borderBottom: '1px solid #E5E7EB',
    whiteSpace: 'nowrap',
    userSelect: 'none',
  };

  const td = {
    padding: '11px 14px',
    fontSize: 13,
    color: '#374151',
    borderBottom: '1px solid #F3F4F6',
    verticalAlign: 'middle',
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>

        {/* ── En-têtes ── */}
        <thead>
          <tr style={{ background: '#F9FAFB' }}>
            <th style={th}>Heure</th>
            <th style={th}>Catégorie</th>
            <th style={th}>Aperçu</th>
            <th style={th}>Statut</th>
            <th style={{ ...th, textAlign: 'right' }}>Latence</th>
            <th style={{ ...th, textAlign: 'right' }}>Tokens</th>
            <th style={{ ...th, textAlign: 'right' }}>Tools</th>
          </tr>
        </thead>

        {/* ── Lignes ── */}
        <tbody>
          {events.map((ev, i) => {
            const s = STATUS[ev.status] ?? STATUS.success;
            return (
              <tr
                key={ev.id}
                style={{ background: i % 2 === 0 ? '#ffffff' : '#FAFAFA' }}
                onMouseEnter={e => e.currentTarget.style.background = '#F5F3FF'}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#ffffff' : '#FAFAFA'}
              >
                {/* Heure */}
                <td style={{ ...td, fontFamily: 'ui-monospace, monospace', fontSize: 12, color: '#9CA3AF', whiteSpace: 'nowrap' }}>
                  {ev.time}
                </td>

                {/* Catégorie — badge violet */}
                <td style={td}>
                  <span style={{
                    background: '#EDE9FE',
                    color: '#5B21B6',
                    borderRadius: 5,
                    padding: '2px 8px',
                    fontSize: 11,
                    fontWeight: 500,
                    whiteSpace: 'nowrap',
                  }}>
                    {ev.category}
                  </span>
                </td>

                {/* Aperçu — tronqué, en italique */}
                <td style={{ ...td, color: '#9CA3AF', fontStyle: 'italic', maxWidth: 160, overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {ev.preview}
                </td>

                {/* Statut — pill colorée */}
                <td style={td}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    background: s.bg,
                    color: s.color,
                    borderRadius: 5,
                    padding: '3px 9px',
                    fontSize: 11,
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot, flexShrink: 0 }} />
                    {s.label}
                  </span>
                </td>

                {/* Latence — rouge si critique */}
                <td style={{ ...td, textAlign: 'right', fontFamily: 'ui-monospace, monospace', fontSize: 12, color: latencyColor(ev.latency_ms), whiteSpace: 'nowrap' }}>
                  {formatLatency(ev.latency_ms)}
                </td>

                {/* Tokens */}
                <td style={{ ...td, textAlign: 'right', fontFamily: 'ui-monospace, monospace', fontSize: 12, whiteSpace: 'nowrap' }}>
                  {formatTokens(ev.tokens)}
                </td>

                {/* Tools count */}
                <td style={{ ...td, textAlign: 'right', color: '#9CA3AF', fontSize: 12 }}>
                  {ev.tools}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default AuditTrailTable;