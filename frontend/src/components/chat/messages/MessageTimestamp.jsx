export default function MessageTimestamp({ time }) {
  if (!time) return null;

  return <span className="chat-message-time">{time}</span>;
}