import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Cpu,
  Database,
  Loader2,
  Search,
  Sparkles,
} from "lucide-react";

import ToolCallRow from "./ToolCallRow";
import "./ToolGroup.css";

export default function ToolGroup({
  step,
  expanded,
  onToggle,
}) {
  const done = step >= 4;

  const tools = [
    {
      name: "analysis",
      label: "Analyse de votre demande",
      status: step > 0 || done ? "success" : "running",
      result: step > 0 || done ? "Terminé" : "En cours...",
      icon: Search,
    },
    {
      name: "data_lookup",
      label: "Consultation des données",
      status: step > 1 || done ? "success" : step === 1 ? "running" : "pending",
      result: step > 1 || done ? "Terminé" : step === 1 ? "En cours..." : "En attente",
      icon: Database,
    },
    {
      name: "processing",
      label: "Traitement des informations",
      status: step > 2 || done ? "success" : step === 2 ? "running" : "pending",
      result: step > 2 || done ? "Terminé" : step === 2 ? "En cours..." : "En attente",
      icon: Cpu,
    },
    {
      name: "generation",
      label: "Génération de la réponse",
      status: done ? "success" : step === 3 ? "running" : "pending",
      result: done ? "Terminé" : step === 3 ? "En cours..." : "En attente",
      icon: Sparkles,
    },
  ];

  return (
    <div className="tool-group tool-group-ghost">
      <button
        type="button"
        className="tool-group-trigger"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <span className="tool-group-trigger-left">
          {!done ? (
            <Loader2 size={13} className="tool-group-loader" />
          ) : (
            <CheckCircle2 size={13} />
          )}

          <span className="tool-group-title">
            {tools.length} tool calls
          </span>
        </span>

        {expanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
      </button>

      {expanded && (
        <div className="tool-group-content">
          {tools.map((tool) => (
            <ToolCallRow key={tool.name} tool={tool} />
          ))}
        </div>
      )}
    </div>
  );
}