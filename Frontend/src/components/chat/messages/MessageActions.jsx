import { Check, Copy, RefreshCw } from "lucide-react";
import useCopy from "../../../hooks/useCopy";

export default function MessageActions({
  text,
  t,
  onRegenerate,
  showRegenerate = false,
}) {
  const [copied, copy] = useCopy();

  const handleCopy = () => {
    const value =
      typeof text === "string"
        ? text
        : JSON.stringify(text, null, 2);

    copy(value);
  };

  return (
    <div className="chat-message-actions">
      <button
        type="button"
        className="chat-message-action"
        onClick={handleCopy}
      >
        {copied ? <Check size={12} /> : <Copy size={12} />}
        {copied ? t.copied : t.copy}
      </button>

      {showRegenerate && onRegenerate && (
        <button
          type="button"
          className="chat-message-action"
          onClick={onRegenerate}
        >
          <RefreshCw size={12} />
          Regénérer
        </button>
      )}
    </div>
  );
}