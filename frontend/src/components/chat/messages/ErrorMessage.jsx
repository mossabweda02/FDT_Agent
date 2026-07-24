import { AlertTriangle, RefreshCw } from "lucide-react";

export default function ErrorMessage({ text, onRetry }) {
  return (
    <div className="chat-message chat-message-agent fade-up">
      <div className="chat-agent-avatar is-error">
        <AlertTriangle size={16} />
      </div>

      <div className="chat-message-content">
        <div className="chat-bubble chat-bubble-error">
          <strong>Une erreur est survenue</strong>
          <p>{text}</p>

          {onRetry && (
            <button
              type="button"
              className="error-retry-button"
              onClick={onRetry}
            >
              <RefreshCw size={13} />
              Réessayer
            </button>
          )}
        </div>
      </div>
    </div>
  );
}