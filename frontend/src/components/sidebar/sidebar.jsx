import {
  PenSquare,
  Trash2,
  Settings,
} from "lucide-react";

import "./Sidebar.css";
import SidebarHeader from "./SidebarHeader";
import SidebarSection from "./SidebarSection";
import SidebarItem from "./SidebarItem";
import ConversationItem from "./ConversationItem";
import UserSessionCard from "./UserSessionCard";

export default function Sidebar({
  sessions,
  activeId,
  collapsed,
  user,
  onSelect,
  onNewChat,
  onRename,
  onDelete,
  onSettings,
  onClear,
  onExpand,
  onLogout,
  onTogglePin,
  t,
}) {
  const pinnedSessions = sessions.filter((session) => session.pinned);
  const normalSessions = sessions.filter((session) => !session.pinned);

  return (
    <aside className={`app-sidebar ${collapsed ? "is-collapsed" : ""}`}
        onClick={(e) => {
            if (!collapsed) return;
            if (e.target.closest(".user-session-wrapper")) return;
            onExpand?.();
    }}>
      <SidebarHeader collapsed={collapsed} />

      <div className="sidebar-main">
        <SidebarItem
          icon={PenSquare}
          label={t.newChat}
          active={false}
          collapsed={collapsed}
          onClick={onNewChat}
          variant="primary"
        />

        {!collapsed && (
          <>
            <SidebarSection title="Récents" collapsed={collapsed} />

            <div className="sidebar-conversations">
              {sessions.length === 0 ? (
                <p className="sidebar-empty">
                  {t.noHistory || "Aucune conversation"}
                </p>
              ) : (
                <>
                  {pinnedSessions.length > 0 && (
                    <div className="sidebar-pinned-group">
                      <div className="sidebar-subsection-title">Épinglés</div>

                      {[...pinnedSessions].reverse().map((session) => (
                        <ConversationItem
                          key={session.id}
                          session={session}
                          active={session.id === activeId}
                          collapsed={collapsed}
                          onSelect={onSelect}
                          onRename={onRename}
                          onDelete={onDelete}
                          onTogglePin={onTogglePin}
                        />
                      ))}
                    </div>
                  )}

                  <div className="sidebar-normal-group">
                    {pinnedSessions.length > 0 && (
                      <h2 className="sidebar-subsection-title">Récents</h2>
                    )}

                    {[...normalSessions].reverse().map((session) => (
                      <ConversationItem
                        key={session.id}
                        session={session}
                        active={session.id === activeId}
                        collapsed={collapsed}
                        onSelect={onSelect}
                        onRename={onRename}
                        onDelete={onDelete}
                        onTogglePin={onTogglePin}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
            
        {sessions.length > 0 && (
          <SidebarItem
            icon={Trash2}
            label={t.clearHistory || "Clear history"}
            collapsed={collapsed}
            onClick={onClear}
            variant="danger"
          />
        )}
          </>
        )}
      </div>

      <div className="sidebar-bottom">
        <SidebarItem
          icon={Settings}
          label={t.settings}
          collapsed={collapsed}
          onClick={onSettings}
        />

        <UserSessionCard
          user={user}
          collapsed={collapsed}
          onLogout={onLogout}
        />
      </div>
    </aside>
  );
}