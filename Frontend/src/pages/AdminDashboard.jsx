// ─── AdminDashboard.jsx ───────────────────────────────────────────────────────
// Page principale du dashboard admin FDT Agent — Phase 1 Demo.
//
// Ce fichier contient :
//   - Le layout principal (sidebar + contenu)
//   - La section Statut des services
//   - La grille KPI
//   - Le graphique SVG pur (requêtes + coût, zéro dépendance)
//   - Le tableau Audit Trail
//
// INTÉGRATION dans App.jsx (ajout minimal, non destructif) :
//   1. Importer en haut de App.jsx :
//        import AdminDashboard from './pages/AdminDashboard'
//   2. Ajouter en première ligne du composant App() :
//        if (window.location.hash === '#admin') return <AdminDashboard />
//   3. Accéder au dashboard : http://localhost:5173/#admin
//
// Pour revenir au chat : retirer le hash → http://localhost:5173/

import { useState } from 'react';
import AdminSidebar from '../components/admin/AdminSidebar';
import MetricCard    from '../components/admin/MetricCard';
import AuditTrailTable from '../components/admin/AuditTrailTable';
import {
  kpiData,
  servicesStatus,
  dailyMetrics,
  auditEvents,
} from '../data/adminMockData';

// ─────────────────────────────────────────────────────────────────────────────
// Graphique SVG pur — Requêtes journalières + Coût estimé
// Aucune dépendance externe. Remplacer par <AreaChart recharts> en Phase 2.
// ─────────────────────────────────────────────────────────────────────────────
const RequestsChart = ({ data }) => {
  const W   = 800;
  const H   = 200;
  const PAD = { top: 16, right: 56, bottom: 34, left: 46 };
  const iW  = W - PAD.left - PAD.right;
  const iH  = H - PAD.top  - PAD.bottom;

  const maxR = Math.max(...data.map(d => d.requests));
  const maxC = Math.max(...data.map(d => d.cost_usd));

  // Fonctions de mise à l'échelle
  const xPos = (i) => PAD.left + (i / (data.length - 1)) * iW;
  const yReq = (v) => PAD.top  + iH - (v / maxR) * iH;
  const yCost= (v) => PAD.top  + iH - (v / maxC) * iH;

  // Construction des paths SVG
  const reqLine  = data.map((d, i) =>
    `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yReq(d.requests).toFixed(1)}`
  ).join(' ');

  const reqArea  = `${reqLine} L${xPos(data.length-1).toFixed(1)},${(PAD.top+iH).toFixed(1)} L${xPos(0).toFixed(1)},${(PAD.top+iH).toFixed(1)} Z`;

  const costLine = data.map((d, i) =>
    `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yCost(d.cost_usd).toFixed(1)}`
  ).join(' ');

  // Grille Y (3 lignes)
  const gridVals = [0, Math.round(maxR / 2), maxR];

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${W} ${H}`}
      style={{ display: 'block', overflow: 'visible' }}
    >
      <defs>
        <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#7C3AED" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.01" />
        </linearGradient>
      </defs>

      {/* Lignes de grille horizontales */}
      {gridVals.map((v, i) => (
        <line key={i}
          x1={PAD.left} x2={W - PAD.right}
          y1={yReq(v)}  y2={yReq(v)}
          stroke="#F3F4F6" strokeWidth="1"
        />
      ))}

      {/* Zone de remplissage — Requêtes */}
      <path d={reqArea} fill="url(#reqGrad)" />

      {/* Ligne principale — Requêtes (violet) */}
      <path
        d={reqLine}
        fill="none"
        stroke="#7C3AED"
        strokeWidth="2.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Ligne secondaire — Coût estimé (amber, pointillée) */}
      <path
        d={costLine}
        fill="none"
        stroke="#F59E0B"
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
        strokeDasharray="5 3"
      />

      {/* Labels axe Y gauche — Requêtes */}
      {gridVals.map((v, i) => (
        <text key={i}
          x={PAD.left - 8}
          y={yReq(v) + 4}
          textAnchor="end"
          fill="#9CA3AF"
          fontSize="11"
          fontFamily="system-ui, sans-serif"
        >
          {v}
        </text>
      ))}

      {/* Labels axe Y droite — Coût ($) */}
      {[0, maxC / 2, maxC].map((v, i) => (
        <text key={i}
          x={W - PAD.right + 8}
          y={yCost(v) + 4}
          textAnchor="start"
          fill="#F59E0B"
          fontSize="11"
          fontFamily="system-ui, sans-serif"
          opacity="0.75"
        >
          ${v.toFixed(1)}
        </text>
      ))}

      {/* Labels axe X — dates (tous les 7 jours) */}
      {data.map((d, i) =>
        (i % 7 === 0 || i === data.length - 1) ? (
          <text key={i}
            x={xPos(i)}
            y={H - 6}
            textAnchor="middle"
            fill="#9CA3AF"
            fontSize="11"
            fontFamily="system-ui, sans-serif"
          >
            {d.label}
          </text>
        ) : null
      )}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Carte statut d'un service (Anthropic LLM / Azure Synapse / Audit Trail)
// ─────────────────────────────────────────────────────────────────────────────
const ServiceCard = ({ label, detail }) => (
  <div style={{
    background: '#fff',
    borderRadius: 10,
    border: '1px solid #E5E7EB',
    padding: '15px 18px',
    flex: 1,
    minWidth: 180,
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
      <span style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>{label}</span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#059669', fontWeight: 500 }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#10B981', display: 'inline-block', boxShadow: '0 0 4px rgba(16,185,129,0.5)' }} />
        Opérationnel
      </span>
    </div>
    <div style={{ fontSize: 11, color: '#9CA3AF' }}>{detail}</div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Page principale
// ─────────────────────────────────────────────────────────────────────────────
const AdminDashboard = () => {
  // activePage pilote la sidebar — Phase 1 : visuel uniquement
  const [activePage, setActivePage] = useState('overview');

  // Styles partagés pour les titres de section
  const sectionTitle = {
    margin: '0 0 12px',
    fontSize: 11,
    fontWeight: 600,
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    userSelect: 'none',
  };

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      background: '#F8F7FF',           // Fond légèrement teinté violet
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
    }}>

      {/* ── Sidebar ── */}
      <AdminSidebar activePage={activePage} onPageChange={setActivePage} />

      {/* ── Contenu principal ── */}
      <main style={{ flex: 1, overflow: 'auto', minWidth: 0 }}>

        {/* Header sticky */}
        <div style={{
          background: '#fff',
          borderBottom: '1px solid #E5E7EB',
          padding: '16px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}>
          {/* Titre */}
          <div>
            <h1 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#111827', letterSpacing: '-0.2px' }}>
              FDT Agent · Admin Dashboard
            </h1>
            <p style={{ margin: '2px 0 0', fontSize: 11.5, color: '#9CA3AF' }}>
              Monitoring métier · Données de démonstration
            </p>
          </div>

          {/* Badges header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              background: '#FEF3C7', color: '#92400E',
              borderRadius: 6, padding: '4px 10px',
              fontSize: 11, fontWeight: 600,
            }}>
              ⚠ Demo Data
            </span>
            <span style={{
              background: '#EDE9FE', color: '#5B21B6',
              borderRadius: 6, padding: '4px 10px',
              fontSize: 11, fontWeight: 600,
            }}>
              30 derniers jours
            </span>
          </div>
        </div>

        {/* Sections */}
        <div style={{ padding: '26px 28px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* ── 1. Statut des services ── */}
          <section>
            <h2 style={sectionTitle}>Statut des services</h2>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {servicesStatus.map(s => (
                <ServiceCard key={s.id} label={s.label} detail={s.detail} />
              ))}
            </div>
          </section>

          {/* ── 2. KPI Grid ── */}
          <section>
            <h2 style={sectionTitle}>Métriques clés · 30j</h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: 12,
            }}>
              {kpiData.map(kpi => (
                <MetricCard key={kpi.id} {...kpi} />
              ))}
            </div>
          </section>

          {/* ── 3. Graphique requêtes + coût ── */}
          <section>
            <div style={{
              background: '#fff',
              borderRadius: 12,
              border: '1px solid #E5E7EB',
              padding: '20px 22px',
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}>
              {/* En-tête du graphique */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#111827' }}>
                    Requêtes journalières
                  </h3>
                  <p style={{ margin: '3px 0 0', fontSize: 11.5, color: '#9CA3AF' }}>
                    Volume agent · 30 jours
                  </p>
                </div>
                {/* Légende */}
                <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#7C3AED' }}>
                    <span style={{ width: 14, height: 3, background: '#7C3AED', display: 'inline-block', borderRadius: 2 }} />
                    Requêtes
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#F59E0B' }}>
                    <span style={{ width: 14, borderTop: '2px dashed #F59E0B', display: 'inline-block' }} />
                    Coût ($)
                  </span>
                </div>
              </div>

              {/* SVG Chart */}
              <RequestsChart data={dailyMetrics} />
            </div>
          </section>

          {/* ── 4. Audit Trail ── */}
          <section>
            <div style={{
              background: '#fff',
              borderRadius: 12,
              border: '1px solid #E5E7EB',
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              overflow: 'hidden',
            }}>
              {/* En-tête du tableau */}
              <div style={{
                padding: '16px 22px',
                borderBottom: '1px solid #E5E7EB',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#111827' }}>
                    Audit Trail
                  </h3>
                  <p style={{ margin: '3px 0 0', fontSize: 11.5, color: '#9CA3AF' }}>
                    Échanges anonymisés · Aperçu uniquement · Pas de données brutes
                  </p>
                </div>
                <span style={{ fontSize: 12, color: '#9CA3AF' }}>
                  {auditEvents.length} événements
                </span>
              </div>

              {/* Tableau */}
              <AuditTrailTable events={auditEvents} />
            </div>
          </section>

          {/* ── Footer ── */}
          <footer style={{ textAlign: 'center', fontSize: 11, color: '#CBD5E1', paddingBottom: 8 }}>
            FDT Agent Admin Dashboard · Phase 1 · Données de démonstration uniquement
          </footer>

        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;