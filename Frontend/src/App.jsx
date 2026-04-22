/**
 * Agent-FDT — App.jsx (v3.0)
 * ─────────────────────────────────────────────────────────────────
 * Phase 1 — Améliorations UI/UX :
 *  1. Mode clair amélioré (couleurs, contrastes, ombres)
 *  2. Gestion individuelle des conversations (renommer / supprimer)
 *  3. Suppression de l'indicateur "Connecté" dans la navbar
 *  4. Alignement à gauche des réponses de l'agent
 *  5. i18n via fichiers JSON externes (fr.json / en.json)
 *  6. Préservation de "Effacer l'historique"
 */

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Search, Database, Cpu, CheckCircle, Copy, Check,
  Settings, X, Sun, Moon, Monitor, Globe,
  MessageSquare, History, Sparkles, Send,
  PanelLeftClose, PanelLeftOpen,
  BarChart3, Users, FolderOpen, Timer,
  Plus, Trash2, Bot, MoreHorizontal, Pencil,
} from "lucide-react";

// ═══════════════════════════════════════════════════════════════════
// 1. INTERNATIONALISATION (i18n)
//    Centralisé ici ; les fichiers fr.json / en.json sont également
//    générés dans /src/i18n/ pour une intégration future avec
//    react-i18next ou i18next.
// ═══════════════════════════════════════════════════════════════════
const T = {
  fr: {
    appName:         "Agent-FDT",
    appSub:          "Analytics Agent",
    settings:        "Paramètres",
    history:         "Historique",
    noHistory:       "Aucune conversation",
    newChat:         "Nouvelle conversation",
    clearHistory:    "Effacer l'historique",
    rename:          "Renommer",
    delete:          "Supprimer",
    renameTitle:     "Renommer la conversation",
    renamePlaceholder: "Nouveau nom…",
    renameConfirm:   "Valider",
    renameCancel:    "Annuler",
    welcomeTitle:    "Que souhaitez-vous savoir ?",
    welcomeSub:      "Posez une question sur vos feuilles de temps, projets ou ressources Metam.",
    placeholder:     "Posez votre question sur les feuilles de temps...",
    footer:          "Agent-FDT · Agent Analytique Metam · Entrée pour envoyer",
    thinking:        "Processus de réflexion",
    thinkingDone:    "— terminé",
    thinkingStep:    "étape",
    typingLabel:     "En train de répondre...",
    suggestionLabel: "Suggestions contextuelles",
    copy:            "Copier",
    copied:          "Copié !",
    errorMsg:        "Erreur de connexion. Vérifiez que le backend tourne sur le port 8000.",
    themeLabel:      "Thème",
    langLabel:       "Langue",
    fontLabel:       "Taille du texte",
    themeDark:       "Sombre",
    themeLight:      "Clair",
    themeSystem:     "Système",
    steps: [
      "Analyse de la question",
      "Interrogation de la base",
      "Traitement et synthèse",
      "Génération de la réponse",
    ],
    quickTiles: [
      { label: "Heures / mois",  q: "Combien d'heures ont été saisies en janvier 2026 ?" },
      { label: "Top projets",    q: "Top 3 projets par heures en 2026 ?" },
      { label: "Par employé",    q: "Heures par employé en janvier 2026 ?" },
      { label: "Rentabilité",    q: "Quels sont les projets les plus rentables ?" },
    ],
  },
  en: {
    appName:         "Agent-FDT",
    appSub:          "Analytics Agent",
    settings:        "Settings",
    history:         "History",
    noHistory:       "No conversations yet",
    newChat:         "New conversation",
    clearHistory:    "Clear history",
    rename:          "Rename",
    delete:          "Delete",
    renameTitle:     "Rename conversation",
    renamePlaceholder: "New name…",
    renameConfirm:   "Confirm",
    renameCancel:    "Cancel",
    welcomeTitle:    "What would you like to know?",
    welcomeSub:      "Ask a question about your timesheets, projects, or Metam resources.",
    placeholder:     "Ask your question about timesheets...",
    footer:          "Agent-FDT · Metam Analytics Agent · Press Enter to send",
    thinking:        "Thinking process",
    thinkingDone:    "— complete",
    thinkingStep:    "step",
    typingLabel:     "Typing a response...",
    suggestionLabel: "Contextual suggestions",
    copy:            "Copy",
    copied:          "Copied!",
    errorMsg:        "Connection error. Make sure the backend is running on port 8000.",
    themeLabel:      "Theme",
    langLabel:       "Language",
    fontLabel:       "Font size",
    themeDark:       "Dark",
    themeLight:      "Light",
    themeSystem:     "System",
    steps: [
      "Analysing the question",
      "Querying the database",
      "Processing & synthesis",
      "Generating the response",
    ],
    quickTiles: [
      { label: "Hours / month",  q: "How many hours were logged in January 2026?" },
      { label: "Top projects",   q: "Top 3 projects by hours in 2026?" },
      { label: "By employee",    q: "Hours per employee in January 2026?" },
      { label: "Profitability",  q: "Which projects are the most profitable?" },
    ],
  },
};

// ═══════════════════════════════════════════════════════════════════
// 2. DÉTECTION DE REQUÊTE CONVERSATIONNELLE vs ANALYTIQUE
// ═══════════════════════════════════════════════════════════════════
const CONV_PATTERNS = [
  /^(bonjour|salut|hello|hi|hey|bonsoir|coucou|good\s*(morning|evening|afternoon|day))/i,
  /^(présente[-\s]?toi|qui\s+(es[-\s]?tu|êtes[-\s]?vous)|what\s+are\s+you|who\s+are\s+you)/i,
  /^(merci|thank(s|\s+you)|de\s+rien|avec\s+plaisir|pas\s+de\s+souci)/i,
  /^(ok|okay|d'accord|parfait|super|génial|great|cool|compris|understood)/i,
  /^(comment\s+(vas[-\s]?tu|ça\s+va|allez[-\s]?vous|are\s+you\s+doing))/i,
  /^(aide[-\s]?moi|help(\s+me)?|qu['']est[-\s]ce\s+que\s+tu\s+(fais|peux|es)|what\s+can\s+you\s+do)/i,
  /^(au\s+revoir|bye|à\s+bientôt|see\s+you)/i,
];

const ANALYTICAL_KEYWORDS = [
  "heure", "heures", "hours", "projet", "projets", "project", "projects",
  "employé", "employés", "employee", "employees", "tâche", "tâches", "task",
  "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
  "septembre", "octobre", "novembre", "décembre",
  "january", "february", "march", "april", "june", "july", "august",
  "september", "october", "november", "december",
  "combien", "how many", "quel", "quels", "top", "rentable", "rentabilité",
  "saisie", "saisies", "feuille", "rapport", "mois", "trimestre",
  "quarter", "année", "year", "total", "somme", "sum", "average", "moyenne",
  "prj-", "budget", "coût", "cost", "margin", "marge",
];

function isConversational(q) {
  const lower = q.trim().toLowerCase();
  if (ANALYTICAL_KEYWORDS.some(kw => lower.includes(kw))) return false;
  if (CONV_PATTERNS.some(p => p.test(lower))) return true;
  const wordCount = lower.replace(/[?!.,]/g, "").split(/\s+/).filter(Boolean).length;
  return wordCount <= 4;
}

// ═══════════════════════════════════════════════════════════════════
// CSS GLOBAL
// ═══════════════════════════════════════════════════════════════════
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  html, body { height: 100%; overflow: hidden; }
  #root {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    border-inline: none !important;
    min-height: 100vh;
    height: 100vh;
    display: flex !important;
    flex-direction: column !important;
  }

  :root {
    --pri:      #6C4CFC;
    --acc:      #E537FF;
    --pri-dim:  rgba(108,76,252,0.15);
    --pri-dim2: rgba(108,76,252,0.25);
    --grad:     linear-gradient(135deg, #6C4CFC, #E537FF);
    --bg:       #07060E;
    --bg2:      #0D0B1A;
    --bg3:      #131126;
    --surface:  rgba(255,255,255,0.04);
    --glass:    rgba(255,255,255,0.05);
    --border:   rgba(108,76,252,0.22);
    --border2:  rgba(255,255,255,0.07);
    --text:     #EEEAF8;
    --text2:    #9D98B8;
    --text3:    #5A5673;
    --success:  #22c55e;
    --danger:   #ef4444;
    --radius:   14px;
    --radius-sm:8px;
    --font:     'Outfit', sans-serif;
    --mono:     'JetBrains Mono', monospace;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.18);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.24);
  }

  /* ─── Mode Clair amélioré ─── */
  [data-theme="light"] {
    --bg:      #F5F3FF;
    --bg2:     #FFFFFF;
    --bg3:     #EDE9FF;
    --surface: rgba(108,76,252,0.06);
    --glass:   rgba(255,255,255,0.92);
    --border:  rgba(108,76,252,0.22);
    --border2: rgba(108,76,252,0.12);
    --text:    #1A1535;
    --text2:   #5A4E8A;
    --text3:   #9D98B8;
    --shadow-sm: 0 1px 4px rgba(108,76,252,0.08);
    --shadow-md: 0 4px 16px rgba(108,76,252,0.12);
    --shadow-lg: 0 8px 32px rgba(108,76,252,0.16);
  }

  body { background: var(--bg); font-family: var(--font); color: var(--text); }

  ::-webkit-scrollbar { width: 3px; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }

  @keyframes fadeUp  { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:none} }
  @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
  @keyframes pulse   { 0%,100%{opacity:.3;transform:scale(.8)} 50%{opacity:1;transform:scale(1.1)} }
  @keyframes spin    { to{transform:rotate(360deg)} }
  @keyframes slideIn { from{transform:translateX(-6px);opacity:0} to{transform:none;opacity:1} }
  @keyframes popIn   { from{transform:scale(.94);opacity:0} to{transform:none;opacity:1} }
  @keyframes blink   { 0%,100%{opacity:.2} 50%{opacity:1} }

  .fade-up  { animation: fadeUp  .3s ease forwards; }
  .fade-in  { animation: fadeIn  .2s ease forwards; }
  .slide-in { animation: slideIn .25s ease forwards; }
  .pop-in   { animation: popIn   .2s cubic-bezier(.34,1.56,.64,1) forwards; }

  textarea:focus, input:focus, button:focus { outline: none; }
  button { cursor: pointer; font-family: var(--font); }
  textarea { font-family: var(--font); resize: none; }

  /* Contexte menu */
  .ctx-menu {
    position: absolute;
    right: 0; top: calc(100% + 4px);
    background: var(--bg2);
    border: 1px solid var(--border2);
    border-radius: 10px;
    overflow: hidden;
    z-index: 50;
    box-shadow: var(--shadow-lg);
    min-width: 140px;
    animation: popIn .15s cubic-bezier(.34,1.56,.64,1) forwards;
  }
  .ctx-item {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px; font-size: 12px;
    color: var(--text2); background: transparent;
    border: none; width: 100%; text-align: left;
    transition: background .12s, color .12s;
  }
  .ctx-item:hover { background: var(--surface); color: var(--text); }
  .ctx-item.danger:hover { background: rgba(239,68,68,.08); color: var(--danger); }
`;

// ═══════════════════════════════════════════════════════════════════
// UTILITAIRES
// ═══════════════════════════════════════════════════════════════════
const fmt = d =>
  new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(d);

const genId = () => Date.now() + Math.random();

// ═══════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════
async function callAgent(question) {
  const r = await fetch("http://127.0.0.1:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const d = await r.json();
  return d.answer ?? d.response ?? JSON.stringify(d);
}

async function fetchSuggestions(question) {
  try {
    const r = await fetch("http://127.0.0.1:8000/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!r.ok) return [];
    return (await r.json()).suggestions ?? [];
  } catch {
    return [];
  }
}

// ═══════════════════════════════════════════════════════════════════
// HOOK useCopy
// ═══════════════════════════════════════════════════════════════════
function useCopy() {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(text => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, []);
  return [copied, copy];
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : ThinkingProcess
// ═══════════════════════════════════════════════════════════════════
function ThinkingProcess({ step, expanded, onToggle, lang }) {
  const done = step >= 4;
  const labels = T[lang].steps;
  const ICONS = [Search, Database, Cpu, CheckCircle];
  return (
    <div style={{
      background: "var(--glass)", border: "1px solid var(--border)",
      borderRadius: "var(--radius)", overflow: "hidden",
      backdropFilter: "blur(12px)", marginBottom: 12,
      boxShadow: "var(--shadow-sm)",
    }}>
      <button onClick={onToggle} style={{
        width: "100%", display: "flex", alignItems: "center",
        gap: 10, padding: "10px 14px", background: "transparent",
        border: "none", color: "var(--text2)", fontSize: 12,
      }}>
        <div style={{
          width: 6, height: 6, borderRadius: "50%",
          background: done ? "var(--success)" : "var(--pri)",
          boxShadow: `0 0 8px ${done ? "var(--success)" : "var(--pri)"}`,
          animation: done ? "none" : "pulse 1.2s infinite",
        }} />
        <span style={{ fontWeight: 500, color: "var(--text2)" }}>
          {T[lang].thinking}{" "}
          {done
            ? T[lang].thinkingDone
            : `(${T[lang].thinkingStep} ${Math.min(step + 1, 4)}/4)`}
        </span>
        <span style={{ marginLeft: "auto", fontSize: 10 }}>{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div style={{ padding: "0 14px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
          {labels.map((label, i) => {
            const Icon = ICONS[i];
            const isActive  = i === step && !done;
            const isDone    = i < step || done;
            const isPending = i > step && !done;
            return (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "7px 10px", borderRadius: "var(--radius-sm)",
                background: isActive ? "var(--pri-dim)" : isDone ? "rgba(34,197,94,0.06)" : "transparent",
                border: `1px solid ${isActive ? "var(--border)" : isDone ? "rgba(34,197,94,.15)" : "transparent"}`,
                opacity: isPending ? 0.35 : 1, transition: "all .3s",
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 7, flexShrink: 0,
                  background: isActive ? "var(--pri-dim)" : isDone ? "rgba(34,197,94,.12)" : "var(--surface)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {isActive
                    ? <div style={{ width: 13, height: 13, border: "2px solid var(--pri)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin .8s linear infinite" }} />
                    : <Icon size={13} color={isDone ? "var(--success)" : "var(--text3)"} />
                  }
                </div>
                <span style={{ fontSize: 12, color: isActive ? "var(--text)" : isDone ? "#86efac" : "var(--text2)" }}>
                  {label}
                </span>
                {isDone && <CheckCircle size={11} color="var(--success)" style={{ marginLeft: "auto" }} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : TypingIndicator
// ═══════════════════════════════════════════════════════════════════
function TypingIndicator({ lang }) {
  return (
    <div className="fade-up" style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "flex-start" }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10, flexShrink: 0,
        background: "var(--grad)", display: "flex", alignItems: "center",
        justifyContent: "center", fontSize: 15,
        boxShadow: "0 4px 12px rgba(108,76,252,.35)",
      }}>⏱</div>
      <div style={{
        padding: "13px 16px", background: "var(--glass)",
        border: "1px solid var(--border2)", borderRadius: "4px 16px 16px 16px",
        backdropFilter: "blur(12px)", display: "flex", alignItems: "center", gap: 10,
        boxShadow: "var(--shadow-sm)",
      }}>
        <span style={{ fontSize: 13, color: "var(--text2)" }}>{T[lang].typingLabel}</span>
        <div style={{ display: "flex", gap: 4 }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{
              width: 5, height: 5, borderRadius: "50%", background: "var(--pri)",
              animation: `blink 1.2s ${i * 0.2}s ease-in-out infinite`,
            }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANTS : Bulles de messages
// ═══════════════════════════════════════════════════════════════════
function UserBubble({ text, time, lang }) {
  const [copied, copy] = useCopy();
  const [hov, setHov] = useState(false);
  return (
    <div className="fade-up" style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20, gap: 8, alignItems: "flex-end" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
        <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{ position: "relative" }}>
          {hov && (
            <button onClick={() => copy(text)} style={{
              position: "absolute", top: -30, right: 0, zIndex: 10,
              background: "var(--bg2)", border: "1px solid var(--border2)",
              borderRadius: 6, padding: "3px 8px", fontSize: 11,
              color: "var(--text2)", display: "flex", alignItems: "center", gap: 4,
              boxShadow: "var(--shadow-sm)",
            }}>
              {copied ? <Check size={10} /> : <Copy size={10} />}
              {copied ? T[lang].copied : T[lang].copy}
            </button>
          )}
          <div style={{
            maxWidth: 480, padding: "11px 16px",
            background: "var(--grad)", borderRadius: "16px 16px 4px 16px",
            color: "#fff", fontSize: 14, lineHeight: 1.65,
            boxShadow: "0 6px 24px rgba(108,76,252,.3)",
          }}>{text}</div>
        </div>
        <span style={{ fontSize: 10, color: "var(--text3)", display: "flex", alignItems: "center", gap: 4 }}>
          <Timer size={9} />{time}
        </span>
      </div>
    </div>
  );
}

function AgentBubble({ text, time, lang }) {
  const [copied, copy] = useCopy();
  const [hov, setHov] = useState(false);

  const renderText = raw => {
    const s = typeof raw === "string" ? raw : JSON.stringify(raw);
    return s.split("\n").map((line, i) => {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return (
        <p key={i} style={{ margin: i === 0 ? 0 : "5px 0 0" }}>
          {parts.map((p, j) =>
            p.startsWith("**") && p.endsWith("**")
              ? <strong key={j} style={{ color: "var(--acc)", fontWeight: 600 }}>{p.slice(2, -2)}</strong>
              : p
          )}
        </p>
      );
    });
  };

  return (
    /* ─── Alignement à gauche (justifyContent retiré) ─── */
    <div className="fade-up" style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "flex-start" }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10, flexShrink: 0,
        background: "var(--grad)", display: "flex", alignItems: "center",
        justifyContent: "center", fontSize: 15,
        boxShadow: "0 4px 12px rgba(108,76,252,.35)",
      }}>⏱</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, maxWidth: 640, flex: 1 }}>
        <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{ position: "relative" }}>
          {hov && (
            <button onClick={() => copy(typeof text === "string" ? text : JSON.stringify(text))} style={{
              position: "absolute", top: -30, left: 0, zIndex: 10,
              background: "var(--bg2)", border: "1px solid var(--border2)",
              borderRadius: 6, padding: "3px 8px", fontSize: 11,
              color: "var(--text2)", display: "flex", alignItems: "center", gap: 4,
              boxShadow: "var(--shadow-sm)",
            }}>
              {copied ? <Check size={10} /> : <Copy size={10} />}
              {copied ? T[lang].copied : T[lang].copy}
            </button>
          )}
          <div style={{
            padding: "12px 16px", background: "var(--glass)",
            border: "1px solid var(--border2)", borderRadius: "4px 16px 16px 16px",
            backdropFilter: "blur(12px)", fontSize: 14, lineHeight: 1.7, color: "var(--text)",
            /* ─── Alignement texte à gauche ─── */
            textAlign: "left",
            boxShadow: "var(--shadow-sm)",
          }}>
            {renderText(text)}
          </div>
        </div>
        <span style={{ fontSize: 10, color: "var(--text3)", paddingLeft: 2, display: "flex", alignItems: "center", gap: 4 }}>
          <Timer size={9} />{time}
        </span>
      </div>
    </div>
  );
}

function ErrorBubble({ text }) {
  return (
    <div className="fade-up" style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "flex-start" }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10,
        background: "rgba(239,68,68,.12)", display: "flex",
        alignItems: "center", justifyContent: "center", fontSize: 14,
      }}>⚠️</div>
      <div style={{
        padding: "12px 16px", background: "rgba(239,68,68,.07)",
        border: "1px solid rgba(239,68,68,.2)", borderRadius: "4px 16px 16px 16px",
        fontSize: 13, color: "#fca5a5", lineHeight: 1.6, maxWidth: 520,
        textAlign: "left",
      }}>{text}</div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Écran d'accueil
// ═══════════════════════════════════════════════════════════════════
function WelcomeScreen({ onSend, lang }) {
  const tiles = T[lang].quickTiles;
  const ICONS = [Timer, FolderOpen, Users, BarChart3];
  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      gap: 40, padding: "40px 24px", textAlign: "center",
    }}>
      <div>
        <div style={{
          width: 72, height: 72, borderRadius: 20, margin: "0 auto 20px",
          background: "var(--grad)", display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 32,
          boxShadow: "0 0 48px rgba(108,76,252,.4)",
        }}>⏱</div>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 10, color: "var(--text)" }}>
          {T[lang].welcomeTitle}
        </h1>
        <p style={{ color: "var(--text2)", fontSize: 14, maxWidth: 380, lineHeight: 1.6 }}>
          {T[lang].welcomeSub}
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, maxWidth: 480, width: "100%" }}>
        {tiles.map((t, i) => {
          const Icon = ICONS[i];
          return (
            <button key={i} onClick={() => onSend(t.q)} style={{
              background: "var(--glass)", border: "1px solid var(--border2)",
              borderRadius: "var(--radius)", padding: "12px 14px",
              textAlign: "left", transition: "all .2s", backdropFilter: "blur(10px)",
              boxShadow: "var(--shadow-sm)",
            }}
              onMouseEnter={e => { e.currentTarget.style.background = "var(--pri-dim)"; e.currentTarget.style.borderColor = "var(--pri)"; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "var(--shadow-md)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "var(--glass)"; e.currentTarget.style.borderColor = "var(--border2)"; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "var(--shadow-sm)"; }}
            >
              <Icon size={16} color="var(--pri)" style={{ marginBottom: 6 }} />
              <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text)", marginBottom: 2 }}>{t.label}</div>
              <div style={{ fontSize: 11, color: "var(--text2)", lineHeight: 1.4 }}>{t.q}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Suggestions contextuelles
// ═══════════════════════════════════════════════════════════════════
function ContextSuggestions({ suggestions, onSend, lang }) {
  if (!suggestions.length) return null;
  return (
    <div className="fade-up" style={{ padding: "0 0 16px", paddingLeft: 42 }}>
      <p style={{ fontSize: 11, color: "var(--text3)", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
        <Sparkles size={11} color="var(--pri)" /> {T[lang].suggestionLabel}
      </p>
      <div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}>
        {suggestions.map((s, i) => (
          <button key={i} onClick={() => onSend(s)} className="pop-in" style={{
            background: "var(--glass)", border: "1px solid var(--border)",
            borderRadius: 20, padding: "5px 12px", color: "var(--text2)",
            fontSize: 12, transition: "all .15s",
            animationDelay: `${i * 0.06}s`, backdropFilter: "blur(8px)",
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--pri)"; e.currentTarget.style.color = "var(--text)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text2)"; }}
          >{s}</button>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Modal de renommage
// ═══════════════════════════════════════════════════════════════════
function RenameModal({ session, onConfirm, onCancel, lang }) {
  const [value, setValue] = useState(session.title);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  function handleKey(e) {
    if (e.key === "Enter") onConfirm(value.trim() || session.title);
    if (e.key === "Escape") onCancel();
  }

  return (
    <div className="fade-in" style={{
      position: "fixed", inset: 0, zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center",
      background: "rgba(0,0,0,.55)", backdropFilter: "blur(8px)",
    }} onClick={e => e.target === e.currentTarget && onCancel()}>
      <div className="pop-in" style={{
        width: 380, background: "var(--bg2)",
        border: "1px solid var(--border)", borderRadius: 16,
        overflow: "hidden", boxShadow: "var(--shadow-lg)",
        padding: 20,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <Pencil size={14} color="var(--pri)" />
          <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>{T[lang].renameTitle}</span>
        </div>
        <input
          ref={inputRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder={T[lang].renamePlaceholder}
          style={{
            width: "100%", padding: "9px 12px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, color: "var(--text)", fontSize: 13,
            marginBottom: 14,
          }}
        />
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onCancel} style={{
            padding: "7px 14px", borderRadius: 8, border: "1px solid var(--border2)",
            background: "transparent", color: "var(--text2)", fontSize: 12,
          }}>{T[lang].renameCancel}</button>
          <button onClick={() => onConfirm(value.trim() || session.title)} style={{
            padding: "7px 16px", borderRadius: 8, border: "none",
            background: "var(--grad)", color: "#fff", fontSize: 12, fontWeight: 500,
          }}>{T[lang].renameConfirm}</button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Sidebar
//   - Menu contextuel "..." par conversation (Renommer / Supprimer)
//   - "Effacer l'historique" global conservé
// ═══════════════════════════════════════════════════════════════════
function Sidebar({ sessions, activeId, onSelect, onNewChat, onClear,
                   onRename, onDelete, collapsed, lang }) {
  const [openMenuId, setOpenMenuId] = useState(null);
  const menuRef = useRef(null);

  // Fermer le menu au clic extérieur
  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpenMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div style={{
      width: collapsed ? 0 : 252, minWidth: collapsed ? 0 : 252,
      height: "100%", background: "var(--bg2)",
      borderRight: "1px solid var(--border2)",
      display: "flex", flexDirection: "column",
      overflow: "hidden", transition: "width .3s, min-width .3s", flexShrink: 0,
    }}>
      {!collapsed && (
        <>
          {/* Branding */}
          <div style={{ padding: "16px 16px 12px", borderBottom: "1px solid var(--border2)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, background: "var(--grad)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>⏱</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: "-0.02em", color: "var(--text)" }}>{T[lang].appName}</div>
                <div style={{ fontSize: 10, color: "var(--text3)" }}>{T[lang].appSub}</div>
              </div>
            </div>
          </div>

          {/* Nouvelle conversation */}
          <div style={{ padding: "10px 12px", borderBottom: "1px solid var(--border2)" }}>
            <button onClick={onNewChat} style={{
              width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)",
              background: "var(--pri-dim)", border: "1px solid var(--border)",
              color: "var(--text)", fontSize: 12, fontWeight: 500,
              display: "flex", alignItems: "center", gap: 8, transition: "all .15s",
            }}
              onMouseEnter={e => { e.currentTarget.style.background = "var(--pri-dim2)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "var(--pri-dim)"; }}
            >
              <Plus size={12} color="var(--pri)" /> {T[lang].newChat}
            </button>
          </div>

          {/* Liste des sessions */}
          <div style={{ padding: "12px 12px 6px", flex: 1, overflowY: "auto" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <History size={12} color="var(--text3)" />
              <span style={{ fontSize: 11, color: "var(--text3)", fontWeight: 500, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                {T[lang].history}
              </span>
            </div>

            {sessions.length === 0
              ? <p style={{ fontSize: 12, color: "var(--text3)", padding: "8px", fontStyle: "italic" }}>
                  {T[lang].noHistory}
                </p>
              : [...sessions].reverse().map((session, i) => {
                  const isActive = session.id === activeId;
                  const isMenuOpen = openMenuId === session.id;
                  return (
                    <div key={session.id} style={{ position: "relative", marginBottom: 2 }}>
                      <button
                        onClick={() => { setOpenMenuId(null); onSelect(session.id); }}
                        className="slide-in"
                        style={{
                          width: "100%", textAlign: "left",
                          padding: "8px 34px 8px 10px", borderRadius: 8, display: "block",
                          background: isActive ? "var(--pri-dim)" : "transparent",
                          border: `1px solid ${isActive ? "var(--border)" : "transparent"}`,
                          color: isActive ? "var(--text)" : "var(--text2)",
                          fontSize: 12, lineHeight: 1.4, transition: "all .15s",
                          animationDelay: `${i * 0.04}s`,
                        }}
                        onMouseEnter={e => {
                          if (!isActive) { e.currentTarget.style.background = "var(--surface)"; e.currentTarget.style.color = "var(--text)"; }
                        }}
                        onMouseLeave={e => {
                          if (!isActive) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--text2)"; }
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                          <MessageSquare size={11} style={{ marginTop: 2, flexShrink: 0, color: isActive ? "var(--pri)" : "var(--text3)" }} />
                          <div style={{ overflow: "hidden", flex: 1 }}>
                            <div style={{
                              overflow: "hidden", textOverflow: "ellipsis",
                              display: "-webkit-box", WebkitLineClamp: 2,
                              WebkitBoxOrient: "vertical",
                            }}>{session.title}</div>
                            <div style={{ fontSize: 10, color: "var(--text3)", marginTop: 2 }}>
                              {session.time} · {session.messages.filter(m => m.role !== "error").length / 2 | 0} éch.
                            </div>
                          </div>
                        </div>
                      </button>

                      {/* Bouton "..." menu contextuel */}
                      <div ref={isMenuOpen ? menuRef : null} style={{ position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)" }}>
                        <button
                          onClick={e => { e.stopPropagation(); setOpenMenuId(isMenuOpen ? null : session.id); }}
                          style={{
                            width: 22, height: 22, borderRadius: 5,
                            background: isMenuOpen ? "var(--pri-dim)" : "transparent",
                            border: "none", color: "var(--text3)",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            transition: "all .12s",
                          }}
                          onMouseEnter={e => { e.currentTarget.style.background = "var(--surface)"; e.currentTarget.style.color = "var(--text2)"; }}
                          onMouseLeave={e => { if (!isMenuOpen) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--text3)"; } }}
                        >
                          <MoreHorizontal size={12} />
                        </button>

                        {isMenuOpen && (
                          <div className="ctx-menu" style={{ right: 0, top: "calc(100% + 2px)" }}>
                            <button className="ctx-item" onClick={e => { e.stopPropagation(); setOpenMenuId(null); onRename(session); }}>
                              <Pencil size={11} /> {T[lang].rename}
                            </button>
                            <button className="ctx-item danger" onClick={e => { e.stopPropagation(); setOpenMenuId(null); onDelete(session.id); }}>
                              <Trash2 size={11} /> {T[lang].delete}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
            }
          </div>

          {/* Effacer l'historique global — conservé */}
          {sessions.length > 0 && (
            <div style={{ padding: "8px 12px 12px", borderTop: "1px solid var(--border2)" }}>
              <button onClick={onClear} style={{
                width: "100%", padding: "7px", borderRadius: "var(--radius-sm)",
                background: "transparent", border: "1px solid rgba(239,68,68,.15)",
                color: "rgba(239,68,68,.55)", fontSize: 11,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                transition: "all .15s",
              }}
                onMouseEnter={e => { e.currentTarget.style.background = "rgba(239,68,68,.07)"; e.currentTarget.style.color = "#f87171"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(239,68,68,.55)"; }}
              >
                <Trash2 size={10} /> {T[lang].clearHistory}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Modal de paramètres
//   - Indicateur "Connecté" supprimé du panneau settings
// ═══════════════════════════════════════════════════════════════════
function SettingsModal({ settings, onChange, onClose, lang }) {
  return (
    <div className="fade-in" style={{
      position: "fixed", inset: 0, zIndex: 100,
      display: "flex", alignItems: "center", justifyContent: "center",
      background: "rgba(0,0,0,.6)", backdropFilter: "blur(8px)",
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="pop-in" style={{
        width: 420, background: "var(--bg2)",
        border: "1px solid var(--border)", borderRadius: 20,
        overflow: "hidden", boxShadow: "var(--shadow-lg)",
      }}>
        {/* Header */}
        <div style={{ padding: "18px 20px", borderBottom: "1px solid var(--border2)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Settings size={15} color="var(--pri)" />
            <span style={{ fontWeight: 600, fontSize: 15, color: "var(--text)" }}>{T[lang].settings}</span>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text2)", borderRadius: 6, padding: 4 }}>
            <X size={15} />
          </button>
        </div>

        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 22 }}>
          {/* Thème */}
          <div>
            <label style={{ fontSize: 12, color: "var(--text2)", fontWeight: 500, display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
              <Monitor size={12} /> {T[lang].themeLabel}
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {[
                { v: "dark",   I: Moon,    l: T[lang].themeDark   },
                { v: "light",  I: Sun,     l: T[lang].themeLight  },
                { v: "system", I: Monitor, l: T[lang].themeSystem },
              ].map(o => {
                const active = settings.theme === o.v;
                return (
                  <button key={o.v} onClick={() => onChange("theme", o.v)} style={{
                    padding: "10px 8px", borderRadius: 10,
                    background: active ? "var(--pri-dim)" : "var(--surface)",
                    border: `1px solid ${active ? "var(--pri)" : "var(--border2)"}`,
                    color: active ? "var(--text)" : "var(--text2)",
                    fontSize: 12, display: "flex", flexDirection: "column",
                    alignItems: "center", gap: 5, transition: "all .15s",
                  }}>
                    <o.I size={14} color={active ? "var(--pri)" : "var(--text3)"} />
                    {o.l}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Langue */}
          <div>
            <label style={{ fontSize: 12, color: "var(--text2)", fontWeight: 500, display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
              <Globe size={12} /> {T[lang].langLabel}
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[{ v: "fr", l: "🇫🇷 Français" }, { v: "en", l: "🇬🇧 English" }].map(o => {
                const active = settings.lang === o.v;
                return (
                  <button key={o.v} onClick={() => onChange("lang", o.v)} style={{
                    padding: "10px", borderRadius: 10,
                    background: active ? "var(--pri-dim)" : "var(--surface)",
                    border: `1px solid ${active ? "var(--pri)" : "var(--border2)"}`,
                    color: active ? "var(--text)" : "var(--text2)",
                    fontSize: 13, fontWeight: active ? 500 : 400, transition: "all .15s",
                  }}>{o.l}</button>
                );
              })}
            </div>
          </div>

          {/* Taille du texte */}
          <div>
            <label style={{
              fontSize: 12, color: "var(--text2)", fontWeight: 500, marginBottom: 10,
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <span>{T[lang].fontLabel}</span>
              <span style={{ color: "var(--pri)", fontFamily: "var(--mono)" }}>{settings.fontSize}px</span>
            </label>
            <input type="range" min={12} max={18} step={1} value={settings.fontSize}
              onChange={e => onChange("fontSize", +e.target.value)}
              style={{ width: "100%", accentColor: "var(--pri)" }} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT : Barre de saisie
// ═══════════════════════════════════════════════════════════════════
function InputBar({ value, onChange, onSend, disabled, lang }) {
  function handleChange(e) {
    onChange(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  }
  const active = value.trim() && !disabled;
  return (
    <div style={{
      background: "var(--glass)", border: "1px solid var(--border)",
      borderRadius: 16, padding: "12px 14px",
      display: "flex", alignItems: "flex-end", gap: 10,
      backdropFilter: "blur(16px)", transition: "border-color .2s, box-shadow .2s",
      boxShadow: "var(--shadow-sm)",
    }}
      onFocusCapture={e => { e.currentTarget.style.borderColor = "var(--pri)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(108,76,252,.15)"; }}
      onBlurCapture={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.boxShadow = "var(--shadow-sm)"; }}
    >
      <textarea rows={1} value={value} onChange={handleChange}
        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
        placeholder={T[lang].placeholder}
        style={{
          flex: 1, background: "transparent", border: "none",
          color: "var(--text)", fontSize: 14, lineHeight: 1.5,
          overflow: "auto", maxHeight: 120, minHeight: 22,
        }} />
      <button disabled={!active} onClick={onSend} style={{
        width: 38, height: 38, borderRadius: 10, border: "none",
        background: active ? "var(--grad)" : "var(--surface)",
        color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
        transition: "all .2s", flexShrink: 0, opacity: active ? 1 : 0.4,
        boxShadow: active ? "0 4px 16px rgba(108,76,252,.4)" : "none",
      }}
        onMouseEnter={e => { if (active) e.currentTarget.style.transform = "scale(1.06)"; }}
        onMouseLeave={e => { e.currentTarget.style.transform = "none"; }}
      >
        <Send size={15} />
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSANT RACINE : App
// ═══════════════════════════════════════════════════════════════════
export default function App() {
  const [sessions,      setSessions]      = useState([]);
  const [activeId,      setActiveId]      = useState(null);
  const [input,         setInput]         = useState("");
  const [thinking,      setThinking]      = useState(false);
  const [isConvMode,    setIsConvMode]    = useState(false);
  const [thinkStep,     setThinkStep]     = useState(0);
  const [thinkExpanded, setThinkExpanded] = useState(true);
  const [suggestions,   setSuggestions]   = useState([]);
  const [sidebarOpen,   setSidebarOpen]   = useState(true);
  const [settingsOpen,  setSettingsOpen]  = useState(false);
  const [settings,      setSettings]      = useState({ theme: "dark", lang: "fr", fontSize: 14 });
  const [renamingSession, setRenamingSession] = useState(null);

  const bottomRef = useRef(null);
  const lang      = settings.lang;

  const activeSession = sessions.find(s => s.id === activeId);
  const messages      = activeSession?.messages ?? [];

  // Thème
  useEffect(() => {
    const t = settings.theme === "system"
      ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : settings.theme;
    document.documentElement.setAttribute("data-theme", t);
  }, [settings.theme]);

  // Taille de fonte
  useEffect(() => {
    document.documentElement.style.fontSize = settings.fontSize + "px";
  }, [settings.fontSize]);

  // Scroll automatique
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const changeSetting = (k, v) => setSettings(s => ({ ...s, [k]: v }));

  // ─── Gestion des sessions ──────────────────────────────────────
  function newChat() {
    setActiveId(null);
    setInput("");
    setSuggestions([]);
  }

  function selectSession(id) {
    setActiveId(id);
    setSuggestions([]);
  }

  function clearAllHistory() {
    setSessions([]);
    setActiveId(null);
    setSuggestions([]);
  }

  // ─── Renommer une conversation ─────────────────────────────────
  function handleRenameConfirm(newTitle) {
    if (!renamingSession) return;
    setSessions(prev => prev.map(s =>
      s.id === renamingSession.id ? { ...s, title: newTitle } : s
    ));
    setRenamingSession(null);
  }

  // ─── Supprimer une conversation individuelle ───────────────────
  function handleDeleteSession(sessionId) {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeId === sessionId) {
      setActiveId(null);
      setSuggestions([]);
    }
  }

  // ─── Envoi d'un message ────────────────────────────────────────
  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || thinking) return;

    setInput("");
    setSuggestions([]);

    const now     = new Date();
    const timeStr = fmt(now);

    const conv = isConversational(q);
    setIsConvMode(conv);

    let sessionId = activeId;
    const sessionExists = sessions.some(s => s.id === sessionId);

    if (!sessionId || !sessionExists) {
      sessionId = genId();
      const newSession = {
        id:       sessionId,
        title:    q,
        time:     timeStr,
        messages: [],
      };
      setSessions(prev => [...prev, newSession]);
      setActiveId(sessionId);
    }

    const userMsg = { role: "user", text: q, time: timeStr };
    setSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, messages: [...s.messages, userMsg] }
        : s
    ));

    setThinking(true);
    setThinkStep(0);
    setThinkExpanded(true);

    let stepTimer;
    if (!conv) {
      const DELAYS = [700, 1500, 900];
      let step = 0;
      const advance = () => {
        if (step < DELAYS.length) {
          stepTimer = setTimeout(() => { step++; setThinkStep(step); advance(); }, DELAYS[step]);
        }
      };
      advance();
    }

    try {
      const answer = await callAgent(q);

      if (!conv) {
        clearTimeout(stepTimer);
        setThinkStep(4);
        await new Promise(r => setTimeout(r, 350));
      }

      const agentMsg = { role: "agent", text: answer, time: fmt(new Date()) };
      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, messages: [...s.messages, agentMsg] }
          : s
      ));

      setThinkExpanded(false);

      if (!conv) {
        const sugs = await fetchSuggestions(q);
        setSuggestions(sugs);
      }
    } catch {
      const errMsg = { role: "error", text: T[lang].errorMsg };
      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, messages: [...s.messages, errMsg] }
          : s
      ));
    } finally {
      setThinking(false);
    }
  }

  // ─── Rendu ────────────────────────────────────────────────────
  return (
    <>
      <style>{GLOBAL_CSS}</style>

      {settingsOpen && (
        <SettingsModal
          settings={settings}
          onChange={changeSetting}
          onClose={() => setSettingsOpen(false)}
          lang={lang}
        />
      )}

      {renamingSession && (
        <RenameModal
          session={renamingSession}
          onConfirm={handleRenameConfirm}
          onCancel={() => setRenamingSession(null)}
          lang={lang}
        />
      )}

      <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={selectSession}
          onNewChat={newChat}
          onClear={clearAllHistory}
          onRename={setRenamingSession}
          onDelete={handleDeleteSession}
          collapsed={!sidebarOpen}
          lang={lang}
        />

        {/* Zone principale */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--bg)" }}>

          {/* En-tête — indicateur "Connecté" supprimé */}
          <header style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "12px 20px", background: "rgba(13,11,26,.85)",
            backdropFilter: "blur(16px)", borderBottom: "1px solid var(--border2)", flexShrink: 0,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button onClick={() => setSidebarOpen(o => !o)} style={{
                background: "transparent", border: "none", color: "var(--text2)",
                borderRadius: 8, padding: 6, display: "flex", alignItems: "center", transition: "color .15s",
              }}
                onMouseEnter={e => e.currentTarget.style.color = "var(--text)"}
                onMouseLeave={e => e.currentTarget.style.color = "var(--text2)"}
              >
                {sidebarOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
              </button>

              {!sidebarOpen && (
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 26, height: 26, borderRadius: 7, background: "var(--grad)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>⏱</div>
                  <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: "-0.02em", color: "var(--text)" }}>
                    Agent<span style={{ color: "var(--acc)" }}>-FDT</span>
                  </span>
                </div>
              )}
            </div>

            {/* Bouton Paramètres uniquement (indicateur "Connecté" supprimé) */}
            <button onClick={() => setSettingsOpen(true)} style={{
              background: "var(--surface)", border: "1px solid var(--border2)",
              borderRadius: 8, padding: "6px 10px", color: "var(--text2)",
              display: "flex", alignItems: "center", gap: 5, fontSize: 12, transition: "all .15s",
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--pri)"; e.currentTarget.style.color = "var(--text)"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border2)"; e.currentTarget.style.color = "var(--text2)"; }}
            >
              <Settings size={13} /> {T[lang].settings}
            </button>
          </header>

          {/* Zone de messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "24px 24px 0" }}>
            <div style={{ maxWidth: 760, margin: "0 auto" }}>

              {messages.length === 0 && !thinking
                ? <WelcomeScreen onSend={send} lang={lang} />
                : (
                  <>
                    {messages.map((m, i) => (
                      <div key={i}>
                        {m.role === "user"  && <UserBubble  text={m.text} time={m.time} lang={lang} />}
                        {m.role === "agent" && <AgentBubble text={m.text} time={m.time} lang={lang} />}
                        {m.role === "error" && <ErrorBubble text={m.text} />}
                      </div>
                    ))}

                    {thinking && (
                      isConvMode
                        ? <TypingIndicator lang={lang} />
                        : (
                          <div className="fade-up" style={{ paddingLeft: 42 }}>
                            <ThinkingProcess
                              step={thinkStep}
                              expanded={thinkExpanded}
                              onToggle={() => setThinkExpanded(o => !o)}
                              lang={lang}
                            />
                          </div>
                        )
                    )}

                    {!thinking && <ContextSuggestions suggestions={suggestions} onSend={send} lang={lang} />}
                  </>
                )
              }

              <div ref={bottomRef} />
            </div>
          </div>

          {/* Zone de saisie */}
          <div style={{ padding: "16px 24px 20px", flexShrink: 0 }}>
            <div style={{ maxWidth: 760, margin: "0 auto" }}>
              <InputBar
                value={input}
                onChange={setInput}
                onSend={() => send()}
                disabled={thinking}
                lang={lang}
              />
              <p style={{ fontSize: 11, color: "var(--text3)", textAlign: "center", marginTop: 8 }}>
                {T[lang].footer}
              </p>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}