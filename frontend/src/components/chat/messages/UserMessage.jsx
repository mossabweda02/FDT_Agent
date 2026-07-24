import MessageActions from "./MessageActions";
import MessageTimestamp from "./MessageTimestamp";

export default function UserMessage({ text, time, t }) {
  return (
    <div className="chat-message chat-message-user fade-up">
      <div className="chat-message-content">
        <div className="chat-bubble chat-bubble-user">
          {text}
        </div>

        <div className="chat-message-meta">
          <MessageTimestamp time={time} />
          <MessageActions text={text} t={t} />
        </div>
      </div>
    </div>
  );
}