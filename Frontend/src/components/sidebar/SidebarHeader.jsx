import { Timer } from "lucide-react";

export default function SidebarHeader({ collapsed }) {
  return (
    <div className={`sidebar-header ${collapsed ? "is-collapsed" : ""}`}>
      <div className={`sidebar-logo ${collapsed ? "is-collapsed" : ""}`}>
        <Timer size={18} />
      </div>

      {!collapsed && (
        <div className="sidebar-brand">
          <strong>FDT Agent</strong>
          <span>Assistant IA</span>
        </div>
      )}
    </div>
  );
}