/**
 * Module: pages/AuthPage
 * =======================
 * Page de connexion Microsoft Entra ID.
 *
 * Déclenche le flux de connexion MSAL via loginRedirect().
 */

import { useState } from "react";
import "../styles/AuthPage.css";
import metamWhite from "../assets/metam-white.svg";
import DotField from "../components/DotField";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../auth/msalConfig";

function MicrosoftLogo() {
  return (
    <svg className="auth-ms-logo" viewBox="0 0 21 21" aria-hidden="true">
      <rect x="1" y="1" width="9" height="9" fill="#F25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
      <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
      <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
    </svg>
  );
}

export default function AuthPage() {
  const { instance } = useMsal();
  const [loading, setLoading] = useState(false);

  async function handleMicrosoftSignIn() {
    setLoading(true);

    try {
      await instance.loginRedirect(loginRequest);
    } catch (error) {
      console.error("[AuthPage] Microsoft sign-in failed:", error);
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <DotField
        className="auth-dot-field"
        dotRadius={2}
        dotSpacing={13}
        bulgeStrength={70}
        glowRadius={180}
        sparkle={false}
        waveAmplitude={0}
        cursorRadius={520}
        cursorForce={0.12}
        bulgeOnly
        gradientFrom="rgba(168, 85, 247, 0.72)"
        gradientTo="rgba(180, 151, 207, 0.5)"
        glowColor="rgba(168, 85, 247, 0.35)"
      />

      <header className="auth-header">
        <img src={metamWhite} alt="Metam" className="auth-logo" />
      </header>

      <section className="auth-visual-panel" aria-hidden="true">
        <div className="auth-hero-content">
          <div className="auth-kicker">
            <span className="auth-kicker-dot" />
            FDT Agent · Assistant IA feuilles de temps
          </div>

          <h2>
            Vos feuilles de temps,
            <span>guidées par l’IA.</span>
          </h2>

          <p>
            Créez, vérifiez et gérez vos saisies hebdomadaires via une
            expérience conversationnelle sécurisée.
          </p>
        </div>

        <div className="auth-orbit-card auth-orbit-card-main">
          <div className="auth-card-header">
            <span>Semaine</span>
            <strong>20h</strong>
          </div>

          <div className="auth-week-grid">
            {["Lun", "Mar", "Mer", "Jeu", "Ven"].map((day, index) => (
              <div key={day} className={index < 3 ? "is-filled" : ""}>
                <span>{day}</span>
                <b>{index < 3 ? "8h" : "—"}</b>
              </div>
            ))}
          </div>
        </div>

        <div className="auth-floating-chip chip-one">Projets</div>
        <div className="auth-floating-chip chip-two">Tâches</div>
        <div className="auth-floating-chip chip-three">Validation</div>
      </section>

      <div className="auth-card-zone">
        <section className="auth-card" aria-label="Connexion FDT Agent">
          <span className="auth-badge">
            <span />
            ACCÈS SÉCURISÉ
          </span>

          <h1>Connexion à FDT Agent</h1>

          <p className="auth-subtitle">
            Connectez-vous avec votre compte Microsoft Metam pour accéder à vos
            projets, tâches et feuilles de temps autorisés.
          </p>

          <button
            className="auth-ms-button"
            onClick={handleMicrosoftSignIn}
            disabled={loading}
          >
            {loading ? <span className="auth-spinner" /> : <MicrosoftLogo />}
            {loading ? "Redirection..." : "Continuer avec Microsoft"}
          </button>

          <div className="auth-restricted-note">
            <span className="auth-lock-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <rect x="4" y="10" width="16" height="10" rx="2" />
                <path d="M8 10V7a4 4 0 0 1 8 0v3" />
              </svg>
            </span>

            <p>
              Accès réservé aux membres de l’équipe Metam. Votre session Azure
              AD sera utilisée pour authentifier les requêtes ERP.
            </p>
          </div>
        </section>
      </div>

      <footer className="auth-footer">
        © 2026 Metam Technology · FDT Agent
      </footer>
    </main>
  );
}