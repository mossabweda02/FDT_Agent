import { MessageSquarePlus } from "lucide-react";

export default function EmptyConversation({ t }) {
  return (
    <div className="empty-conversation fade-up">
      <div className="empty-conversation-icon">
        <MessageSquarePlus size={24} />
      </div>

      <h2>{t.emptyConversationTitle}</h2>

      <p>{t.emptyConversationDescription}</p>

      <span>{t.emptyConversationExample}</span>
    </div>
  );
}