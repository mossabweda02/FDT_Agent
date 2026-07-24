export default function SidebarSection({ title, collapsed }) {
  if (collapsed) return null;

  return <div className="sidebar-section-title">{title}</div>;
}