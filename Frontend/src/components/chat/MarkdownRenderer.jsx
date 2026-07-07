import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const BUSINESS_ID_REGEX = /\b(TSK|PRJ|EMP|MAT|RES|CAT)-\d+\b/g;

function normalizeMarkdown(content) {
  const value =
    typeof content === "string"
      ? content
      : JSON.stringify(content, null, 2);

  const lines = value.split("\n");

  return lines
    .map((line) => {
      const trimmed = line.trim();

      const isAlreadyMarkdownList =
        /^[-*+]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed);

      const looksLikeBusinessCode =
        /^(TSK|PRJ|EMP|MAT|RES|CAT)-\d+$/i.test(trimmed);

      if (looksLikeBusinessCode && !isAlreadyMarkdownList) {
        return `- **${trimmed}**`;
      }

      return line;
    })
    .join("\n");
}

function renderWithBusinessBadges(text) {
  const parts = String(text).split(BUSINESS_ID_REGEX);

  if (parts.length === 1) return text;

  const nodes = [];

  for (let i = 0; i < parts.length; i += 3) {
    const before = parts[i];
    const prefix = parts[i + 1];
    const rest = parts[i + 2];

    if (before) nodes.push(before);

    if (prefix && rest) {
      const id = `${prefix}-${rest}`;
      nodes.push(
        <span key={`${id}-${i}`} className={`business-badge badge-${prefix.toLowerCase()}`}>
          {id}
        </span>
      );
    }
  }

  return nodes;
}

export default function MarkdownRenderer({ content }) {
  const normalizedContent = normalizeMarkdown(content);

  return (
    <div className="markdown-renderer">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          text({ children }) {
            return renderWithBusinessBadges(children);
          },
          strong({ children }) {
            return <strong>{renderWithBusinessBadges(children)}</strong>;
          },
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
}