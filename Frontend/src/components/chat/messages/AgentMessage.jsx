import { Bot } from "lucide-react";
import MessageActions from "./MessageActions";
import MessageTimestamp from "./MessageTimestamp";
import MarkdownRenderer from "../MarkdownRenderer";


export default function AgentMessage({
  text,
  time,
  t,
  onRegenerate,
}) {
  return (
    <div className="chat-message chat-message-agent fade-up">
      <div className="chat-agent-avatar">
        <Bot size={17} />
      </div>

      <div className="chat-message-content">
        <div className="chat-bubble chat-bubble-agent">
          <MarkdownRenderer content={text} />
        </div>

        <div className="chat-message-meta chat-agent-actions">
          <MessageTimestamp time={time} />

          <MessageActions
            text={text}
            t={t}
            onRegenerate={onRegenerate}
            showRegenerate
          />
        </div>
      </div>
    </div>
  );
}