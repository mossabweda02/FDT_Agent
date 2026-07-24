import { Bot } from "lucide-react";

export default function TypingMessage({ t }) {
  return (
    <div className="chat-message chat-message-agent fade-up">
      <div className="chat-agent-avatar">
        <Bot size={17} />
      </div>

      <div className="chat-message-content">
        <div className="chat-bubble chat-bubble-agent chat-typing-bubble">
          <span>{t.typingLabel}</span>

          <span className="chat-typing-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </div>
      </div>
    </div>
  );
}