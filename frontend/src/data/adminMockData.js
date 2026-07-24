// ─── adminMockData.js ─────────────────────────────────────────────────────────
// Toutes les données mockées du dashboard admin FDT Agent.
// Phase 1 : aucune connexion backend, aucune DB.
// Pour brancher des vraies données (Phase 2), remplacer chaque export
// par un fetch() dans les hooks correspondants.

// ─── KPI Cards ────────────────────────────────────────────────────────────────
export const kpiData = [
  {
    id: 'requests',
    label: 'Total Requêtes',
    value: '2 847',
    delta: '+12%',
    deltaUp: true,
    accentColor: '#7C3AED',
  },
  {
    id: 'success_rate',
    label: 'Taux de succès',
    value: '94.2%',
    delta: '+0.3%',
    deltaUp: true,
    accentColor: '#10B981',
  },
  {
    id: 'avg_latency',
    label: 'Latence moyenne',
    value: '1 843 ms',
    delta: '−0.2s',
    deltaUp: true,
    accentColor: '#0891B2',
  },
  {
    id: 'cost',
    label: 'Coût estimé',
    value: '$109.23',
    delta: '+5.2%',
    deltaUp: false,
    accentColor: '#F59E0B',
  },
  {
    id: 'tokens_in',
    label: 'Tokens entrée',
    value: '22.2M',
    delta: null,
    deltaUp: null,
    accentColor: '#8B5CF6',
  },
  {
    id: 'tokens_out',
    label: 'Tokens sortie',
    value: '590.7K',
    delta: null,
    deltaUp: null,
    accentColor: '#EC4899',
  },
];

// ─── Statut des services ──────────────────────────────────────────────────────
export const servicesStatus = [
  {
    id: 'llm',
    label: 'Anthropic LLM',
    status: 'operational',
    detail: 'Circuit: CLOSED · 0 failures',
  },
  {
    id: 'db',
    label: 'Azure Synapse',
    status: 'operational',
    detail: 'Ping: 15.7 ms',
  },
  {
    id: 'audit',
    label: 'Audit Trail',
    status: 'operational',
    detail: 'Dernière entrée: il y a 2 min',
  },
];

// ─── Métriques journalières (30 jours) ───────────────────────────────────────
// Génération déterministe (Math.sin) — résultat identique à chaque rendu.
// Le pic entre j11 et j15 reproduit le pattern observé dans les vraies données.
const generateDailyMetrics = () => {
  const data = [];
  const start = new Date('2026-04-13');

  for (let i = 0; i < 30; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const label = `${mm}-${dd}`;

    // Seed déterministe entre 0 et 1
    const seed = Math.abs(Math.sin(i * 7.391));

    // Facteur de pic (reproduit le spike visible dans l'image de référence)
    const spike =
      i >= 11 && i <= 13 ? 4.5 + seed * 0.8 :
      i >= 14 && i <= 15 ? 3.5 + seed * 0.5 :
      i >= 16 && i <= 18 ? 2.0 + seed * 0.4 :
      1.0;

    const requests   = Math.round((55 + seed * 45) * spike);
    const inputT     = Math.round((180000 + seed * 60000) * spike);
    const outputT    = Math.round((18000  + seed * 8000)  * spike);
    const costUsd    = parseFloat((inputT * 0.000003 + outputT * 0.000015).toFixed(2));

    data.push({ label, requests, input_tokens: inputT, output_tokens: outputT, cost_usd: costUsd });
  }

  return data;
};

export const dailyMetrics = generateDailyMetrics();

// ─── Audit Trail (événements anonymisés) ──────────────────────────────────────
// Champs affichés : id court, heure, catégorie, aperçu tronqué, statut,
//                  latence, total tokens, nombre de tools.
// Jamais exposé   : question brute, réponse brute, SQL, outputs tools.
export const auditEvents = [
  { id: 'a1b2', time: '14:32', category: 'Feuilles de temps', preview: 'Répartition heures…',    status: 'success', latency_ms: 1242,  tokens: 2146, tools: 2 },
  { id: 'c3d4', time: '14:28', category: 'Feuilles de temps', preview: 'Heures supplémentai…',   status: 'success', latency_ms: 987,   tokens: 1834, tools: 1 },
  { id: 'e5f6', time: '14:15', category: 'Budget',            preview: 'Budget vs réel Q2…',     status: 'success', latency_ms: 22301, tokens: 4210, tools: 3 },
  { id: 'g7h8', time: '14:09', category: 'Dépenses',          preview: 'Rapport dépenses…',      status: 'error',   latency_ms: 11892, tokens: 890,  tools: 1 },
  { id: 'i9j0', time: '13:58', category: 'HSE',               preview: 'Liste employés HSE…',    status: 'success', latency_ms: 3421,  tokens: 5610, tools: 4 },
  { id: 'k1l2', time: '13:44', category: 'Payroll',           preview: 'Masse salariale…',       status: 'partial', latency_ms: 22423, tokens: 3180, tools: 2 },
  { id: 'm3n4', time: '13:31', category: 'Feuilles de temps', preview: 'Absences par équipe…',   status: 'success', latency_ms: 1105,  tokens: 1920, tools: 2 },
  { id: 'o5p6', time: '13:22', category: 'HSE',               preview: 'Indicateurs sécurité…',  status: 'success', latency_ms: 4801,  tokens: 3340, tools: 3 },
  { id: 'q7r8', time: '13:10', category: 'Budget',            preview: 'Coût moyen par ETP…',    status: 'error',   latency_ms: 24261, tokens: 510,  tools: 1 },
  { id: 's9t0', time: '12:58', category: 'Approvisionnement', preview: 'Fournisseurs top 10…',   status: 'success', latency_ms: 2910,  tokens: 2780, tools: 2 },
];