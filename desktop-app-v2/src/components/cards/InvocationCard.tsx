/**
 * InvocationCard — Card-style display for a summoned creature / invocation.
 *
 * Shows the creature stat block in a dark-fantasy styled card:
 * - Header: name, difficulty badge, creature type + size
 * - Stats grid: STR, AGI, INT, WIL, PER, DEF, HP, SPD
 * - Traits, immunities, attacks, description (collapsible)
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ChevronDown,
  ChevronUp,
  Pencil,
  Trash2,
  Shield,
  Heart,
  Eye,
  Wind,
  Skull,
} from "lucide-react";
import type { Invocation } from "../../hooks/useCreatures";

interface InvocationCardProps {
  invocation: Invocation;
  onEdit?: () => void;
  onDelete?: () => void;
}

/** Map difficulty to a color hint. */
function getDifficultyColor(dif: number): string {
  if (dif <= 10) return "#4ade80";   // green — easy
  if (dif <= 25) return "#c4a35a";   // gold  — moderate
  if (dif <= 50) return "#f97316";   // orange — hard
  if (dif <= 100) return "#ef4444";  // red — deadly
  return "#a855f7";                  // purple — legendary
}

export default function InvocationCard({ invocation, onEdit, onDelete }: InvocationCardProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const difColor = getDifficultyColor(invocation.difficulty);

  const stats = [
    { key: "STR", value: invocation.strength },
    { key: "AGI", value: invocation.agility },
    { key: "INT", value: invocation.intellect },
    { key: "WIL", value: invocation.will },
  ];

  return (
    <div
      className="rounded-lg overflow-hidden transition-shadow hover:shadow-lg"
      style={{
        background: "linear-gradient(135deg, #16213e 0%, #0f3460 100%)",
        borderLeft: `3px solid ${difColor}`,
        boxShadow: `0 0 12px ${difColor}22, inset 0 1px 0 rgba(255,255,255,0.05)`,
      }}
    >
      {/* ── Header ── */}
      <div className="p-4 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-display text-text-primary text-lg leading-tight truncate">
              {invocation.name || t("invocations.unnamed")}
            </h3>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span
                className="text-xs font-bold px-2 py-0.5 rounded-full"
                style={{ backgroundColor: `${difColor}30`, color: difColor }}
              >
                {t("invocations.difficulty")} {invocation.difficulty}
              </span>
              {invocation.creature_type && (
                <span className="text-xs text-text-muted">
                  {invocation.creature_type}
                </span>
              )}
              {invocation.size && (
                <span className="text-xs text-text-muted">
                  · {t("invocations.size")} {invocation.size}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-1 shrink-0">
            {onEdit && (
              <button
                onClick={onEdit}
                className="p-1.5 rounded-lg text-text-muted hover:text-accent hover:bg-accent/10 transition-colors"
                title={t("common.edit")}
              >
                <Pencil size={14} />
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 transition-colors"
                title={t("common.delete")}
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Key stats row ── */}
      <div className="px-4 pb-3">
        <div className="grid grid-cols-4 gap-2">
          <MiniStat icon={<Heart size={12} />} label="HP" value={invocation.health} color="#ef4444" />
          <MiniStat icon={<Shield size={12} />} label="DEF" value={invocation.defense} color="#3b82f6" />
          <MiniStat icon={<Eye size={12} />} label="PER" value={invocation.perception} color="#a855f7" />
          <MiniStat icon={<Wind size={12} />} label="SPD" value={invocation.speed} color="#22d3ee" />
        </div>
      </div>

      {/* ── Core attributes ── */}
      <div className="px-4 pb-3">
        <div className="grid grid-cols-4 gap-2">
          {stats.map((s) => (
            <div
              key={s.key}
              className="bg-background/40 border border-border/50 rounded-md p-1.5 text-center"
            >
              <div className="text-[0.6rem] text-text-muted uppercase tracking-wider">{s.key}</div>
              <div className="text-sm font-bold text-text-primary">{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Attacks summary ── */}
      {invocation.attack_options && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-1.5 text-xs text-text-muted mb-1">
            <Skull size={11} />
            <span className="uppercase tracking-wider font-semibold">{t("invocations.attacks")}</span>
          </div>
          <p className="text-xs text-text-primary leading-relaxed line-clamp-2">
            {invocation.attack_options}
          </p>
        </div>
      )}

      {/* ── Expand/Collapse for details ── */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2 flex items-center justify-center gap-1 text-xs text-text-muted
                   hover:text-accent transition-colors border-t border-border/30"
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? t("invocations.showLess") : t("invocations.showMore")}
      </button>

      {/* ── Expanded details ── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border/30">
          {invocation.traits && (
            <DetailSection label={t("invocations.traits")} text={invocation.traits} />
          )}
          {invocation.immunities && (
            <DetailSection label={t("invocations.immunities")} text={invocation.immunities} />
          )}
          {invocation.special_attacks && (
            <DetailSection label={t("invocations.specialAttacks")} text={invocation.special_attacks} />
          )}
          {invocation.description && (
            <DetailSection label={t("invocations.description")} text={invocation.description} />
          )}
        </div>
      )}
    </div>
  );
}

/* ── Small helpers ── */

function MiniStat({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-background/40 border border-border/50 rounded-md p-1.5 text-center">
      <div className="flex items-center justify-center gap-1 mb-0.5" style={{ color }}>
        {icon}
        <span className="text-[0.6rem] uppercase tracking-wider font-semibold">{label}</span>
      </div>
      <div className="text-sm font-bold text-text-primary">{value}</div>
    </div>
  );
}

function DetailSection({ label, text }: { label: string; text: string }) {
  return (
    <div className="pt-2">
      <div className="text-xs text-accent uppercase tracking-wider font-semibold mb-1">{label}</div>
      <p className="text-xs text-text-primary leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  );
}
