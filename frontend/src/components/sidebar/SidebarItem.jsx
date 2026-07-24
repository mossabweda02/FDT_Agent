export default function SidebarItem({
  icon,
  label,
  active = false,
  collapsed = false,
  variant = "default",
  onClick,
}) {
  const IconComponent = icon;

  return (
    <button
      type="button"
      className={[
        "sidebar-item",
        active ? "is-active" : "",
        collapsed ? "is-collapsed" : "",
        variant === "primary" ? "is-primary" : "",
        variant === "primary" ? "is-primary" : "",
        variant === "danger" ? "is-danger" : "",
      ].join(" ")}
      onClick={onClick}
      title={collapsed ? label : undefined}
    >
      <span className="sidebar-item-icon">
        {IconComponent && <IconComponent size={17} />}
      </span>

      {!collapsed && <span className="sidebar-item-label">{label}</span>}
    </button>
  );
}