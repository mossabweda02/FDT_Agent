/**
 * Module: pages/ChatPage.jsx
 * ==========================
 * Page principale de l'interface conversationnelle FDT Agent.
 *
 * Responsabilités :
 * - gérer les sessions de conversation et l'historique des messages ;
 * - envoyer les questions utilisateur à l'API backend ;
 * - afficher les réponses de l'agent, les erreurs et les suggestions de suivi ;
 * - distinguer les requêtes conversationnelles des requêtes analytiques ;
 * - gérer les paramètres d'interface : thème, langue et taille du texte ;
 * - gérer la sidebar, le renommage et la suppression des conversations ;
 * - exposer une action de déconnexion lorsque `onLogout` est fournie.
 */
 

import { useState, useRef, useEffect } from "react";
import {
  Settings, X, Sun, Moon, Monitor, 
  Globe,Sparkles, ArrowUp, Square, ChevronDown,
  PanelLeftClose, PanelLeftOpen, BarChart3, Users, 
  FolderOpen, Timer, Bot
} from "lucide-react";
import { useTranslation } from "../i18n/useTranslation";
import "../styles/ChatPage.css";
import "../components/sidebar/Sidebar.css";

import Sidebar from "../components/sidebar/Sidebar";
import ToolGroup from "../components/chat/ToolGroup";
import AgentMessage from "../components/chat/messages/AgentMessage";
import UserMessage from "../components/chat/messages/UserMessage";
import TypingMessage from "../components/chat/messages/TypingMessage";
import ErrorMessage from "../components/chat/messages/ErrorMessage";
import ThemeToggle from "../components/ui/ThemeToggle";
import SettingsPanel from "../components/settings/SettingsPanel";

import useChatPreferences from "../hooks/useChatPreferences";
import useSmartAutoScroll from "../hooks/useSmartAutoScroll";
import usePersistentState from "../hooks/usePersistentState";
import useMicrosoftProfilePhoto from "../hooks/useMicrosoftProfilePhoto";

import { callAgent, fetchSuggestions } from "../api/agentApi";

// ═══════════════════════════════════════════════════════════════════
// 2. QUERY CLASSIFICATION — conversational vs analytical
// ═══════════════════════════════════════════════════════════════════

/** Regex patterns that unambiguously signal a conversational (non-data) message. */
const CONV_PATTERNS = [
  /^(bonjour|salut|hello|hi|hey|bonsoir|coucou|good\s*(morning|evening|afternoon|day))/i,
  /^(présente[-\s]?toi|qui\s+(es[-\s]?tu|êtes[-\s]?vous)|what\s+are\s+you|who\s+are\s+you)/i,
  /^(merci|thank(s|\s+you)|de\s+rien|avec\s+plaisir|pas\s+de\s+souci)/i,
  /^(ok|okay|d'accord|parfait|super|génial|great|cool|compris|understood)/i,
  /^(comment\s+(vas[-\s]?tu|ça\s+va|allez[-\s]?vous|are\s+you\s+doing))/i,
  /^(aide[-\s]?moi|help(\s+me)?|qu['']est[-\s]ce\s+que\s+tu\s+(fais|peux|es)|what\s+can\s+you\s+do)/i,
  /^(au\s+revoir|bye|à\s+bientôt|see\s+you)/i,
];

/** Keywords whose presence overrides CONV_PATTERNS and forces analytical mode. */
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

/**
 * Returns true when the query is conversational (should use TypingIndicator)
 * rather than analytical (should use ThinkingProcess with step animation).
 */
function isConversational(q) {
  const lower = q.trim().toLowerCase();
  if (ANALYTICAL_KEYWORDS.some(kw => lower.includes(kw))) return false;
  if (CONV_PATTERNS.some(p => p.test(lower))) return true;
  const wordCount = lower.replace(/[?!.,]/g, "").split(/\s+/).filter(Boolean).length;
  return wordCount <= 4;
}

// ═══════════════════════════════════════════════════════════════════
// 4. UTILITIES
// ═══════════════════════════════════════════════════════════════════

/** Format a Date object as HH:MM (fr-FR locale). */
const fmt = d =>
  new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(d);

/** Generate a unique numeric ID for sessions. */
const genId = () => Date.now() + Math.random();

// ═══════════════════════════════════════════════════════════════════
// 6. SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════════x 

// ─── Welcome screen ────────────────────────────────────────────────

/** Shown when a session has no messages yet. Displays quick-action tiles. */
function WelcomeScreen({ onSend, input, onInputChange, disabled, t, user }) {
  const tiles = t?.quickTiles ?? [];
  const ICONS = [Timer, FolderOpen, Users, BarChart3];

  const firstName = user?.name?.split(" ")?.[0] || "Utilisateur";

  return (
    <section className="chat-home fade-up">
      <div className="chat-home-background" />

      <div className="chat-home-content">
        <div className="chat-home-logo">
          <Timer size={34} />
        </div>

        <div className="chat-home-heading">
          <h1>Bonjour, {firstName}.</h1>
          <p>Comment puis-je vous aider aujourd’hui avec vos feuilles de temps ?</p>
        </div>

        <div className="chat-home-input">
          <InputBar
            value={input}
            onChange={onInputChange}
            onSend={() => onSend()}
            disabled={disabled}
            t={t}
          />
        </div>

        <div className="chat-home-suggestions">
          {tiles.map((tile, index) => {
            const Icon = ICONS[index] || Sparkles;

            return (
              <button
                key={tile.label}
                type="button"
                className="chat-home-suggestion"
                onClick={() => onSend(tile.q)}
              >
                {/* <span className="chat-home-suggestion-icon">
                  <Icon size={15} />
                </span> */}

                <span className="chat-home-suggestion-content">
                  {/* <strong>{tile.label}</strong> */}
                  <small>{tile.q}</small>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/** Follow-up suggestion chips shown after an analytical response. */
function ContextSuggestions({ suggestions, onSend }) {
  if (!suggestions.length) return null;

  return (
    <div className="context-suggestions">
      <div
          className="context-suggestions-list"
          onMouseDown={(e) => {
            const slider = e.currentTarget;
            let isDown = true;
            const startX = e.pageX - slider.offsetLeft;
            const scrollLeft = slider.scrollLeft;

            function onMouseMove(moveEvent) {
              if (!isDown) return;
              moveEvent.preventDefault();
              const x = moveEvent.pageX - slider.offsetLeft;
              const walk = (x - startX) * 1.4;
              slider.scrollLeft = scrollLeft - walk;
            }

            function onMouseUp() {
              isDown = false;
              window.removeEventListener("mousemove", onMouseMove);
              window.removeEventListener("mouseup", onMouseUp);
            }

            window.addEventListener("mousemove", onMouseMove);
            window.addEventListener("mouseup", onMouseUp);
          }}
        >
        {suggestions.slice(0, 4).map((suggestion, index) => (
          <button
            key={`${suggestion}-${index}`}
            type="button"
            className="context-suggestion-pill"
            onClick={() => onSend(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Modals ────────────────────────────────────────────────────────

/** Inline modal for renaming a conversation. Closes on backdrop click or Escape. */
function RenameModal({ session, onConfirm, onCancel, t }) {
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
          <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text)" }}>{t.renameTitle}</span>
        </div>
        <input
          ref={inputRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder={t.renamePlaceholder}
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
          }}>{t.renameCancel}</button>
          <button onClick={() => onConfirm(value.trim() || session.title)} style={{
            padding: "7px 16px", borderRadius: 8, border: "none",
            background: "var(--grad)", color: "#fff", fontSize: 12, fontWeight: 500,
          }}>{t.renameConfirm}</button>
        </div>
      </div>
    </div>
  );
}

/**
 * Settings modal.
 * Controls: theme (dark / light / system), language (FR / EN), font size.
 * Note: the "Connected" status indicator was intentionally removed in v3.0.
 */
function SettingsModal({ settings, onChange, onClose, t }) {
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
            <span style={{ fontWeight: 600, fontSize: 15, color: "var(--text)" }}>{t.settings}</span>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text2)", borderRadius: 6, padding: 4 }}>
            <X size={15} />
          </button>
        </div>

        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 22 }}>
          {/* Theme selector */}
          <div>
            <label style={{ fontSize: 12, color: "var(--text2)", fontWeight: 500, display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
              <Monitor size={12} /> {t.themeLabel}
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {[
                { v: "dark",   I: Moon,    l: t.themeDark   },
                { v: "light",  I: Sun,     l: t.themeLight  },
                { v: "system", I: Monitor, l: t.themeSystem },
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

          {/* Language selector */}
          <div>
            <label style={{ fontSize: 12, color: "var(--text2)", fontWeight: 500, display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
              <Globe size={12} /> {t.langLabel}
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

          {/* Font-size range */}
          <div>
            <label style={{
              fontSize: 12, color: "var(--text2)", fontWeight: 500, marginBottom: 10,
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <span>{t.fontLabel}</span>
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

// ─── Input bar ─────────────────────────────────────────────────────

/** Auto-expanding textarea with a send button. Enter sends; Shift+Enter inserts newline. */
function InputBar({ value, onChange, onSend, onStop, disabled, generating, t, enterToSend = true }) {
  function handleChange(e) {
    onChange(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  }

  const active = value.trim() && !disabled;
  const isGenerating = generating;
  const placeholder = t.inputPlaceholder ?? "Demander à FDT Agent";

  return (
    <div className={`chat-input-box ${active ? "is-active" : ""} ${disabled ? "is-disabled" : ""}`}>
      <textarea
        rows={1}
        value={value}
        onChange={handleChange}
        onKeyDown={e => {
          if (enterToSend && e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        placeholder={placeholder}
        className="chat-input-textarea"
      />

      <button
        disabled={!active && !isGenerating}
        onClick={isGenerating ? onStop : onSend}
        className={`chat-send-button ${active || isGenerating ? "is-active" : ""} ${isGenerating ? "is-generating" : ""}`}
      >
        {isGenerating ? (<Square size={15} fill="currentColor" />) : (<ArrowUp size={18} />)}
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// 8. PAGE COMPONENT — ChatPage (root of this page)
// ═══════════════════════════════════════════════════════════════════

/**
 * ChatPage is the single page of the application.
 * It owns all state: sessions, active session, UI flags, settings.
 * Rendered by App.jsx.
 */
export default function ChatPage({ onLogout, user }) {
  // ─── State ────────────────────────────────────────────────────
  const [sessions,        setSessions]        = usePersistentState("sessions", []);
  const [activeId,        setActiveId]        = usePersistentState("activeId", null);
  const [input,           setInput]           = useState("");
  const [thinking,        setThinking]        = useState(false);
  const [isConvMode,      setIsConvMode]      = useState(false);
  const [thinkStep,       setThinkStep]       = useState(0);
  const [thinkExpanded,   setThinkExpanded]   = useState(false);
  const [suggestions,     setSuggestions]     = useState([]);
  const [sidebarOpen,     setSidebarOpen]     = useState(true);
  const [settingsOpen,    setSettingsOpen]    = useState(false);
  const [settings,        setSettings]        = useState({ theme: "dark", lang: "fr", fontSize: 14 });
  const [renamingSession, setRenamingSession] = useState(null);
  const bottomRef = useRef(null);
  const lang      = settings.lang;
  const { t } = useTranslation(lang);
  const abortControllerRef = useRef(null);
  const { photoUrl: profilePhotoUrl } = useMicrosoftProfilePhoto(Boolean(user?.email));
  const { preferences, updatePreference } = useChatPreferences();

  const activeSession = sessions.find(s => s.id === activeId);
  const messages = activeSession?.messages ?? [];

const {
  containerRef: messagesContainerRef,
  isNearBottom,
  scrollToBottom,
} = useSmartAutoScroll([
  messages.length,
  thinking,
  suggestions.length,
]);
  // ─── Side effects ──────────────────────────────────────────────

  // Apply theme to <html data-theme>
  useEffect(() => {
    const t = settings.theme === "system"
      ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : settings.theme;
    document.documentElement.setAttribute("data-theme", t);
  }, [settings.theme]);

  // Apply font size to <html>
  useEffect(() => {
    document.documentElement.style.fontSize = settings.fontSize + "px";
  }, [settings.fontSize]);

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const changeSetting = (k, v) => setSettings(s => ({ ...s, [k]: v }));

  // ─── Session management ────────────────────────────────────────

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

  function handleRenameConfirm(newTitle) {
    if (!renamingSession) return;
    setSessions(prev => prev.map(s =>
      s.id === renamingSession.id ? { ...s, title: newTitle } : s
    ));
    setRenamingSession(null);
  }

  function handleDeleteSession(sessionId) {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeId === sessionId) {
      setActiveId(null);
      setSuggestions([]);
    }
  }

  function handleTogglePin(sessionId) {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? { ...session, pinned: !session.pinned }
          : session
      )
    );
  }

  // ─── Send a message ────────────────────────────────────────────

  async function send(text) {
  const q = (text ?? input).trim();
  if (!q || thinking) return;

  const controller = new AbortController();
  abortControllerRef.current = controller;

  setInput("");
  setSuggestions([]);

  const now = new Date();
  const timeStr = fmt(now);
  const conv = isConversational(q);
  setIsConvMode(conv);

  let sessionId = activeId;
  const sessionExists = sessions.some((s) => s.id === sessionId);

  if (!sessionId || !sessionExists) {
    sessionId = genId();
    const newSession = {
      id: sessionId,
      title: q,
      time: timeStr,
      messages: [],
    };

    setSessions((prev) => [...prev, newSession]);
    setActiveId(sessionId);
  }

  const userMsg = { role: "user", text: q, time: timeStr };

  setSessions((prev) =>
    prev.map((s) =>
      s.id === sessionId
        ? { ...s, messages: [...s.messages, userMsg] }
        : s
    )
  );

  setThinking(true);
  setThinkStep(0);
  setThinkExpanded(false);

  let stepTimer;

  if (!conv) {
    const DELAYS = [700, 1500, 900];
    let step = 0;

    const advance = () => {
      if (step < DELAYS.length) {
        stepTimer = setTimeout(() => {
          step += 1;
          setThinkStep(step);
          advance();
        }, DELAYS[step]);
      }
    };

    advance();
  }

  try {
    const history =
      sessions.find((s) => s.id === sessionId)?.messages ?? [];

    const answer = await callAgent(
      q,
      sessionId,
      history,
      controller.signal
    );

    if (!conv) {
      clearTimeout(stepTimer);
      setThinkStep(4);
      await new Promise((resolve) => setTimeout(resolve, 350));
    }

    const agentMsg = {
      role: "agent",
      text: answer,
      time: fmt(new Date()),
    };

    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? { ...s, messages: [...s.messages, agentMsg] }
          : s
      )
    );

    setThinkExpanded(false);

    if (!conv) {
      const sugs = await fetchSuggestions(q);
      setSuggestions(sugs);
    }
  } catch (error) {
    if (error.name === "AbortError") {
      clearTimeout(stepTimer);
      return;
    }

    const errMsg = {
      role: "error",
      text: t.errorMsg,
    };

    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? { ...s, messages: [...s.messages, errMsg] }
          : s
      )
    );
  } finally {
    clearTimeout(stepTimer);
    setThinking(false);
    setThinkStep(0);
    setThinkExpanded(false);
    abortControllerRef.current = null;
  }
}

  function regenerateLastAnswer() {
  if (thinking || !activeSession) return;

  const lastUserMessage = [...activeSession.messages]
    .reverse()
    .find((message) => message.role === "user");

  if (!lastUserMessage?.text) return;

  setSessions((prev) =>
    prev.map((session) =>
      session.id === activeId
        ? {
            ...session,
            messages: session.messages.filter(
              (_, index) => index !== session.messages.length - 1
            ),
          }
        : session
    )
  );

  send(lastUserMessage.text);
}

function stopGeneration() {
  if (!abortControllerRef.current) return;

  abortControllerRef.current.abort();
  abortControllerRef.current = null;

  setThinking(false);
  setThinkStep(0);
  setThinkExpanded(false);
}
  // ─── Render ────────────────────────────────────────────────────
  return (
    <>
      {settingsOpen && (
        <SettingsModal
          settings={settings}
          onChange={changeSetting}
          onClose={() => setSettingsOpen(false)}
          t={t}
        />
      )}

      {renamingSession && (
        <RenameModal
          session={renamingSession}
          onConfirm={handleRenameConfirm}
          onCancel={() => setRenamingSession(null)}
          t={t}
        />
      )}

      <div className="chat-shell" style={{ display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeId={activeId}
          collapsed={!sidebarOpen}
          user={{ ...user, photoUrl: profilePhotoUrl,}}          
          onSelect={selectSession}
          onNewChat={newChat}
          onRename={setRenamingSession}
          onDelete={handleDeleteSession}
          onTogglePin={handleTogglePin}
          onSettings={() => setSettingsOpen(true)}
          onClear={clearAllHistory}
          onExpand={() => setSidebarOpen(true)}
          onLogout={onLogout}
          t={t}
        />

        {/* Main area */}
        <div className="chat-main" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* Header — "Connected" indicator removed in v3.0 */}
          <header className="chat-glass-header">
            <div className="chat-header-backdrop" />
            <div className="chat-header-left">
              <button
                type="button"
                className="sidebar-toggle-button"
                onClick={() => setSidebarOpen((open) => !open)}
                aria-label="Basculer la sidebar"
              >
                {sidebarOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
              </button>
            </div>
            <div className="chat-header-actions">
              <ThemeToggle />
            </div>
          </header>

          {/* Message list */}
          <div
            ref={messagesContainerRef}
            className="chat-messages-scroll"
          >
            <div style={{ maxWidth: 760, margin: "0 auto" }}>

              {messages.length === 0 && !thinking
                ?<WelcomeScreen
                    onSend={send}
                    input={input}
                    onInputChange={setInput}
                    disabled={thinking}
                    t={t}
                    user={user}
                  /> 
                : (
                  <>
                    {messages.map((m, i) => (
                      <div key={i}>
                        {m.role === "user" && (
                          <UserMessage
                            text={m.text}
                            time={m.time}
                            t={t}
                          />
                        )}

                        {m.role === "agent" && (
                          <AgentMessage
                            text={m.text}
                            time={m.time}
                            t={t}
                            onRegenerate={regenerateLastAnswer}
                          />
                        )}

                        {m.role === "error" && (
                          <ErrorMessage 
                          text={m.text}
                          onRetry={regenerateLastAnswer}
                          />
                        )}
                      </div>
                    ))}

                    {thinking && (isConvMode ? (<TypingMessage t={t} />) : preferences.showToolCalls ? (
                        <div className="chat-message chat-message-agent fade-up">
                          <div className="chat-agent-avatar">
                            <Bot size={17} />
                          </div>

                          <div className="chat-message-content">
                            <ToolGroup
                              step={thinkStep}
                              expanded={thinkExpanded}
                              onToggle={() => setThinkExpanded((open) => !open)}
                            />
                          </div>
                        </div>
                      ) : (
                        <TypingMessage t={t} />
                      )
                    )}

                  </>
                )
              }

              <div ref={bottomRef} />
            </div>
          </div>
          
          {messages.length > 0 && !isNearBottom && (
            <button
              className="scroll-to-bottom-button"
              onClick={scrollToBottom}
              aria-label="Retour en bas"
            >
              <ChevronDown size={18} />
            </button>
          )}

          {/* Input area */}
          {messages.length > 0 && (
          <div className="chat-composer-zone">
            {preferences.contextSuggestions && !thinking && (
              <ContextSuggestions
                suggestions={suggestions}
                onSend={send}
              />
            )}

            <div className="chat-composer-inner">
              <InputBar
                value={input}
                onChange={setInput}
                onSend={() => send()}
                onStop={stopGeneration}
                disabled={thinking}
                generating={thinking}
                enterToSend={preferences.enterToSend}
                t={t}
              />

              <p className="chat-input-footer">
                {t.footer}
              </p>
            </div>
          </div>
          )}
        </div>
      </div>
      <SettingsPanel
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
      user={user}
      preferences={preferences}
      updatePreference={updatePreference}
    />
    </>
  );
}