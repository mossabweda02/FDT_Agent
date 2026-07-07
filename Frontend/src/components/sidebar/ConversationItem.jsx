import { useEffect, useRef, useState } from "react";
import {
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  Trash2,
} from "lucide-react";

export default function ConversationItem({
  session,
  active,
  collapsed,
  onSelect,
  onRename,
  onDelete,
  onTogglePin,
}) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (collapsed) return null;

  return (
    <div className="conversation-item-wrap">
      <button
        type="button"
        className={`conversation-item ${active ? "is-active" : ""}`}
        onClick={() => onSelect(session.id)}
      >
        <span className="conversation-icon">
          <MessageSquare size={16} />
        </span>

        <span className="conversation-content">
          <strong>{session.title}</strong>
        </span>
      </button>

      <div className="conversation-actions">
        <button
          type="button"
          className={`conversation-pin-button ${session.pinned ? "is-pinned" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin(session.id);
          }}
          title={session.pinned ? "Désépingler" : "Épingler"}
        >
          {session.pinned ? <PinOff size={14} /> : <Pin size={14} />}
        </button>

        <div className="conversation-menu-zone" ref={open ? menuRef : null}>
          <button
            type="button"
            className="conversation-menu-button"
            onClick={(e) => {
              e.stopPropagation();
              setOpen((v) => !v);
            }}
          >
            <MoreHorizontal size={15} />
          </button>

          {open && (
            <div className="conversation-menu">
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onRename(session);
                }}
              >
                <Pencil size={13} />
                Renommer
              </button>

              <button
                type="button"
                className="danger"
                onClick={() => {
                  setOpen(false);
                  onDelete(session.id);
                }}
              >
                <Trash2 size={13} />
                Supprimer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}