import { useState } from "react";
import { Bot, Check } from "lucide-react";
import MessageTimestamp from "./MessageTimestamp";
import { callClarify } from "../../../api/agentApi";

function SingleChoiceQuestion({ question, value, onChange }) {
  const [customMode, setCustomMode] = useState(false);
  const [customValue, setCustomValue] = useState("");

  const isKnownOption = question.options.some((o) => o.value === value);

  return (
    <div className="clarification-question-options clarification-scroll">
      {question.options.map((opt, idx) => (
        <button
          key={opt.value}
          type="button"
          className={`clarification-option ${value === opt.value ? "is-selected" : ""}`}
          onClick={() => { setCustomMode(false); onChange(opt.value); }}
        >
          <span className="clarification-option-index">{idx + 1}</span>
          {opt.label}
        </button>
      ))}

      {question.allow_custom_input && (
        customMode || (value && !isKnownOption) ? (
          <div className="clarification-option clarification-option-custom is-editing">
            <input
              type="text"
              autoFocus
              placeholder="Saisir une valeur..."
              value={value && !isKnownOption ? value : customValue}
              onChange={(e) => { setCustomValue(e.target.value); onChange(e.target.value); }}
            />
          </div>
        ) : (
          <button
            type="button"
            className="clarification-option clarification-option-custom"
            onClick={() => setCustomMode(true)}
          >
            ✏️ Autre chose
          </button>
        )
      )}
    </div>
  );
}

function MultiChoiceQuestion({ question, value, onChange }) {
  const selected = Array.isArray(value) ? value : [];

  const toggle = (optValue) => {
    onChange(
      selected.includes(optValue)
        ? selected.filter((v) => v !== optValue)
        : [...selected, optValue]
    );
  };

  return (
    <div className="clarification-question-options clarification-scroll">
      <div className="clarification-selection-count">
        {selected.length} sélectionné{selected.length > 1 ? "s" : ""}
      </div>

      {question.options.map((opt) => (
        <label key={opt.value} className="clarification-checkbox-row">
          <input
            type="checkbox"
            checked={selected.includes(opt.value)}
            onChange={() => toggle(opt.value)}
          />
          {opt.label}
        </label>
      ))}
    </div>
  );
}

function QuestionInput({ question, value, onChange }) {
  switch (question.type) {
    case "single_choice":
      return <SingleChoiceQuestion question={question} value={value} onChange={onChange} />;
    case "multi_choice":
      return <MultiChoiceQuestion question={question} value={value} onChange={onChange} />;
    case "date_picker":
      return (
        <input
          type="date"
          className="clarification-date-input"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "number_input":
      return (
        <input
          type="number"
          className="clarification-number-input"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "multiline_text":
      return (
        <textarea
          className="clarification-multiline-input"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    default:
      return null;
  }
}

export default function QuestionnaireMessage({ questionnaire, time, onAnswered }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentValue, setCurrentValue] = useState(undefined);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const question = questionnaire.questions[currentIndex];
  const isLastOfBatch = currentIndex === questionnaire.questions.length - 1;

  const hasValue = Array.isArray(currentValue) ? currentValue.length > 0 : Boolean(String(currentValue ?? "").trim());

  const handleNext = async () => {
    if (question.required && !hasValue) return;

    const answer = {
      question_id: question.id,
      value: currentValue,
      is_custom_input: question.allow_custom_input && !question.options.some((o) => o.value === currentValue),
    };

    if (!isLastOfBatch) {
      // Le batch actuel n'est pas épuisé : question suivante, sans appel réseau.
      setCurrentIndex((i) => i + 1);
      setCurrentValue(undefined);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const result = await callClarify(questionnaire.conversation_id, [answer]);
      onAnswered(result); // nouveau questionnaire (cascade) ou confirmation finale
    } catch {
      setError("Une erreur est survenue, veuillez réessayer.");
      setSubmitting(false);
    }
  };

  return (
    <div className="chat-message chat-message-agent fade-up">
      <div className="chat-agent-avatar"><Bot size={17} /></div>
      <div className="chat-message-content">
        <div className="chat-bubble chat-bubble-agent chat-bubble-questionnaire">
          <div className="clarification-header">
            <span className="clarification-progress">
              {currentIndex + 1} / {questionnaire.questions.length}
            </span>
          </div>

          <p className="clarification-question-title">{question.label}</p>

          <QuestionInput question={question} value={currentValue} onChange={setCurrentValue} />

          {error && <p className="clarification-error">{error}</p>}

          <button
            type="button"
            className="clarification-submit-button"
            disabled={(question.required && !hasValue) || submitting}
            onClick={handleNext}
          >
            {submitting ? "Envoi..." : isLastOfBatch ? "Continuer" : "Suivant"}
          </button>
        </div>
        <div className="chat-message-meta"><MessageTimestamp time={time} /></div>
      </div>
    </div>
  );
}