import {
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";

export default function ToolCallRow({ tool }) {
  const Icon = tool.icon;

  return (
    <div className={`tool-call-row is-${tool.status}`}>
      <span className="tool-call-icon">
        {tool.status === "running" ? (
          <Loader2 size={14} className="tool-call-loader" />
        ) : tool.status === "success" ? (
          <CheckCircle2 size={14} />
        ) : (
          <Circle size={14} />
        )}
      </span>

      <span className="tool-call-main">
        <span className="tool-call-name">
          <Icon size={13} />
          {tool.label}
        </span>
      </span>

      <span className="tool-call-result">{tool.result}</span>
    </div>
  );
}