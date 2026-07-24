import { useState } from "react";
import {
  LogOut,
  User,
  Settings,
  Moon,
  HelpCircle,
  Home,
} from "lucide-react";

export default function UserSessionCard({
  user,
  collapsed,
  onLogout,
}) {
  const [open, setOpen] = useState(false);

  const name = user?.name || "Utilisateur";
  const email = user?.email || "";

  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div
      className={`user-session-wrapper ${collapsed ? "is-collapsed" : ""}`}
      onClick={(e) => e.stopPropagation()}
      onMouseEnter={() => collapsed && setOpen(true)}
      onMouseLeave={() => collapsed && setOpen(false)}
    >
      <div className={`user-session-card ${collapsed ? "is-collapsed" : ""}`}>
        <div className="user-avatar">
          {user?.photoUrl ? (
            <img src={user.photoUrl} alt={name} />
          ) : (
            initials || "U"
          )}
        </div>

        {!collapsed && (
          <>
            <div className="user-session-info">
              <strong>{name}</strong>
              {email && <span>{email}</span>}
            </div>

            {onLogout && (
              <button
                type="button"
                className="user-logout-button"
                onClick={onLogout}
                title="Déconnexion"
              >
                <LogOut size={16} />
              </button>
            )}
          </>
        )}
      </div>

      {collapsed && open && (
        <div className="user-profile-popover">
          <div className="profile-popover-header">
            <div className="profile-popover-avatar">
              {user?.photoUrl ? (
                <img src={user.photoUrl} alt={name} />
              ) : (
                initials || "U"
              )}
            </div>

            <div className="profile-popover-identity">
              <strong>{name}</strong>
              {email && <span>{email}</span>}
            </div>
          </div>

          <div className="profile-popover-menu">
            <button type="button">
              <User size={15} />
              Profil
            </button>

            <button type="button">
              <Settings size={15} />
              Paramètres
            </button>

            <button type="button">
              <Moon size={15} />
              Apparence
            </button>

            <button type="button">
              <HelpCircle size={15} />
              Assistance
            </button>

            <button type="button">
              <Home size={15} />
              Accueil
            </button>
          </div>

          {onLogout && (
            <button
              type="button"
              className="profile-popover-logout"
              onClick={onLogout}
            >
              <LogOut size={15} />
              Se déconnecter
            </button>
          )}
        </div>
      )}
    </div>
  );
}