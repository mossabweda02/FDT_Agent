// ─── AdminSidebar.jsx ─────────────────────────────────────────────────────────
// Sidebar de navigation du dashboard admin.
// Phase 1 : les items Audit Trail et Token & Coûts sont visuels uniquement.
// Phase 2+ : ajouter React Router et connecter les liens.
//
// Props :
//   activePage   string        — id de la page active ('overview'|'audit'|'tokens')
//   onPageChange (id) => void  — callback de navigation

const NAV_ITEMS = [
  {
    id: 'overview',
    label: 'Overview',
    // SVG inline : icône grille 2×2
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="1" y="1" width="6" height="6" rx="1.5"/>
        <rect x="9" y="1" width="6" height="6" rx="1.5"/>
        <rect x="1" y="9" width="6" height="6" rx="1.5"/>
        <rect x="9" y="9" width="6" height="6" rx="1.5"/>
      </svg>
    ),
  },
  {
    id: 'audit',
    label: 'Audit Trail',
    // SVG inline : icône liste
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <line x1="2" y1="4" x2="14" y2="4"/>
        <line x1="2" y1="8" x2="10" y2="8"/>
        <line x1="2" y1="12" x2="12" y2="12"/>
      </svg>
    ),
  },
  {
    id: 'tokens',
    label: 'Token & Coûts',
    // SVG inline : icône graphe
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="1,12 5,7 9,9 15,3"/>
        <line x1="1" y1="15" x2="15" y2="15"/>
      </svg>
    ),
  },
];

const AdminSidebar = ({ activePage, onPageChange }) => {
  return (
    <aside style={{
      width: 220,
      minHeight: '100vh',
      background: '#0F172A',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      position: 'sticky',
      top: 0,
      height: '100vh',
      overflowY: 'auto',
    }}>

      {/* ── Brand ── */}
      <div style={{
        padding: '22px 18px 18px',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Logo carré violet */}
          <div style={{
            width: 34,
            height: 34,
            borderRadius: 9,
            background: 'linear-gradient(135deg, #6D28D9, #A855F7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 15,
            fontWeight: 800,
            color: '#fff',
            letterSpacing: '-0.5px',
            flexShrink: 0,
          }}>
            F
          </div>
          <div>
            <div style={{ color: '#F1F5F9', fontSize: 14, fontWeight: 600, lineHeight: 1.3 }}>
              FDT Agent
            </div>
            <div style={{ color: '#475569', fontSize: 11, marginTop: 1 }}>
              Admin · Demo
            </div>
          </div>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav style={{ padding: '14px 10px', flex: 1 }}>
        <div style={{ fontSize: 10, color: '#334155', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', padding: '0 10px', marginBottom: 6 }}>
          Navigation
        </div>

        {NAV_ITEMS.map(item => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 12px',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                marginBottom: 2,
                background: isActive ? 'rgba(124, 58, 237, 0.18)' : 'transparent',
                color: isActive ? '#C4B5FD' : '#64748B',
                fontSize: 13.5,
                fontWeight: isActive ? 600 : 400,
                textAlign: 'left',
                transition: 'all 0.12s ease',
                // Bordure gauche active
                borderLeft: isActive ? '2.5px solid #7C3AED' : '2.5px solid transparent',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                  e.currentTarget.style.color = '#94A3B8';
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#64748B';
                }
              }}
            >
              <span style={{ opacity: isActive ? 1 : 0.6, flexShrink: 0 }}>
                {item.icon}
              </span>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* ── Agent Status (bas de sidebar) ── */}
      <div style={{
        padding: '14px 18px',
        borderTop: '1px solid rgba(255,255,255,0.07)',
      }}>
        {/* Indicateur statut */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          {/* Dot avec animation pulse simulée via border */}
          <div style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: '#10B981',
            boxShadow: '0 0 0 3px rgba(16,185,129,0.2)',
            flexShrink: 0,
          }} />
          <span style={{ color: '#D1FAE5', fontSize: 12, fontWeight: 500 }}>
            Agent opérationnel
          </span>
        </div>
        {/* Détail version */}
        <div style={{ color: '#334155', fontSize: 11, paddingLeft: 16 }}>
          FDT Agent · Phase 1 · Demo
        </div>
      </div>

    </aside>
  );
};

export default AdminSidebar;