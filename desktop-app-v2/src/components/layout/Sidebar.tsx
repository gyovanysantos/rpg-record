import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard,
  Users,
  Sparkles,
  Star,
  Dices,
  Swords,
  Mic,
  FileText,
  BookOpen,
  Settings,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useAppStore } from "../../stores/appStore";

interface NavItem {
  path: string;
  labelKey: string;
  icon: React.ReactNode;
  dmOnly?: boolean;
}

const navItems: NavItem[] = [
  { path: "/", labelKey: "sidebar.dashboard", icon: <LayoutDashboard size={20} /> },
  { path: "/characters", labelKey: "sidebar.characters", icon: <Users size={20} /> },
  { path: "/spells", labelKey: "sidebar.spells", icon: <Sparkles size={20} /> },
  { path: "/talents", labelKey: "sidebar.talents", icon: <Star size={20} /> },
  { path: "/dice", labelKey: "sidebar.dice", icon: <Dices size={20} /> },
  { path: "/initiative", labelKey: "sidebar.initiative", icon: <Swords size={20} />, dmOnly: true },
  { path: "/recorder", labelKey: "sidebar.recorder", icon: <Mic size={20} />, dmOnly: true },
  { path: "/transcripts", labelKey: "sidebar.transcripts", icon: <FileText size={20} />, dmOnly: true },
  { path: "/narrator", labelKey: "sidebar.narrator", icon: <BookOpen size={20} />, dmOnly: true },
  { path: "/settings", labelKey: "sidebar.settings", icon: <Settings size={20} /> },
];

export default function Sidebar() {
  const { t } = useTranslation();
  const role = useAppStore((s) => s.role);
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  const visibleItems = navItems.filter(
    (item) => !item.dmOnly || role === "dm"
  );

  return (
    <aside
      className={`h-screen bg-surface border-r border-border flex flex-col
                   transition-all duration-300 ${collapsed ? "w-16" : "w-52"}`}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between border-b border-border">
        {!collapsed && (
          <span className="font-display text-accent text-base tracking-wider">
            RPG Record
          </span>
        )}
        <button
          onClick={toggleSidebar}
          className="text-text-muted hover:text-text-primary transition-colors"
        >
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg transition-colors
               ${
                 isActive
                   ? "bg-accent/15 text-accent border-l-2 border-accent"
                   : "text-text-muted hover:text-text-primary hover:bg-background/50"
               } ${collapsed ? "justify-center px-0 mx-1" : ""}`
            }
            title={collapsed ? t(item.labelKey) : undefined}
          >
            {item.icon}
            {!collapsed && (
              <span className="text-base">{t(item.labelKey)}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Role indicator */}
      <div className="p-4 border-t border-border">
        {!collapsed && (
          <span className="text-sm text-text-muted uppercase tracking-wider">
            {role === "dm" ? t("roles.dm") : t("roles.player")}
          </span>
        )}
      </div>
    </aside>
  );
}
