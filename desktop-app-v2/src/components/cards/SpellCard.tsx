/**
 * SpellCard — A flippable card showing a spell.
 *
 * Front: tradition color accent, name, rank badge, short description, casting tracker
 * Back:  full description text
 *
 * Click to flip. Cast button decrements castings.
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { Zap, RotateCcw, Moon } from "lucide-react";
import { useTranslation } from "react-i18next";
import { getTraditionColor, getRankLabel, getRankBadgeColor } from "../../utils/traditionColors";
import type { Spell, CharacterSpell } from "../../hooks/useSpells";

interface SpellCardProps {
  spell: Spell | CharacterSpell;
  /** If true, show casting tracker + cast button */
  interactive?: boolean;
  /** Called when the "Cast" button is clicked */
  onCast?: () => void;
  /** Called when the card is clicked (for picker mode) */
  onSelect?: () => void;
  /** Visual: is this spell selected in a picker */
  selected?: boolean;
  /** Compact mode for smaller grids */
  compact?: boolean;
}

function isCharacterSpell(s: Spell | CharacterSpell): s is CharacterSpell {
  return "max_castings" in s;
}

export default function SpellCard({
  spell,
  interactive = false,
  onCast,
  onSelect,
  selected = false,
  compact = false,
}: SpellCardProps) {
  const { t } = useTranslation();
  const [flipped, setFlipped] = useState(false);

  const color = getTraditionColor(spell.tradition);
  const hasTracking = interactive && isCharacterSpell(spell);
  const spent = hasTracking && spell.current_castings <= 0;

  // Truncate description for the front face
  const shortDesc =
    spell.description.length > 120
      ? spell.description.slice(0, 117) + "…"
      : spell.description;

  function handleClick() {
    if (onSelect) {
      onSelect();
      return;
    }
    setFlipped((f) => !f);
  }

  function handleCast(e: React.MouseEvent) {
    e.stopPropagation();
    if (onCast && hasTracking && spell.current_castings > 0) {
      onCast();
    }
  }

  return (
    <div
      className="perspective-1000"
      style={{ perspective: "1000px" }}
    >
      <motion.div
        className={`relative cursor-pointer ${compact ? "h-56" : "h-72"} w-full`}
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.5, type: "spring", stiffness: 260, damping: 20 }}
        style={{ transformStyle: "preserve-3d" }}
        onClick={handleClick}
      >
        {/* ── FRONT FACE ────────────────────────────── */}
        <div
          className={`absolute inset-0 rounded-lg p-4 flex flex-col backface-hidden overflow-hidden
            ${spent ? "opacity-50 grayscale" : ""}
            ${selected ? "ring-2 ring-accent" : ""}
          `}
          style={{
            backfaceVisibility: "hidden",
            background: `linear-gradient(135deg, #16213e 0%, #0f3460 100%)`,
            borderLeft: `3px solid ${color}`,
            boxShadow: spent
              ? "none"
              : `0 0 12px ${color}22, inset 0 1px 0 rgba(255,255,255,0.05)`,
          }}
        >
          {/* Header: tradition + rank */}
          <div className="flex items-center justify-between mb-2">
            <span
              className="text-sm font-semibold uppercase tracking-wider"
              style={{ color }}
            >
              {spell.tradition}
            </span>
            <span
              className="text-sm font-bold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: getRankBadgeColor(spell.rank), color: "#e0d6c8" }}
            >
              {getRankLabel(spell.rank, true)}
            </span>
          </div>

          {/* Name */}
          <h3
            className={`font-display text-text-primary ${compact ? "text-base" : "text-lg"} leading-tight mb-2`}
          >
            {spell.name}
          </h3>

          {/* Short description */}
          <p className="text-text-muted text-sm leading-relaxed flex-1 overflow-hidden">
            {shortDesc}
          </p>

          {/* Footer: casting tracker or flip hint */}
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-border">
            {hasTracking ? (
              <>
                <div className="flex items-center gap-1.5 text-sm">
                  {spent ? (
                    <Moon size={14} className="text-text-muted" />
                  ) : (
                    <Zap size={14} style={{ color }} />
                  )}
                  <span className={spent ? "text-text-muted" : "text-text"}>
                    {spell.current_castings}/{spell.max_castings}
                  </span>
                </div>
                <button
                  onClick={handleCast}
                  disabled={spent}
                  className={`text-sm px-3 py-1 rounded font-semibold transition-colors
                    ${spent
                      ? "bg-surface text-text-muted cursor-not-allowed"
                      : "bg-accent/20 text-accent hover:bg-accent/30"
                    }`}
                >
                  {spent ? t("spells.spent") : t("spells.cast")}
                </button>
              </>
            ) : (
              <span className="text-text-muted text-sm italic">
                {t("spells.clickToFlip")}
              </span>
            )}
          </div>
        </div>

        {/* ── BACK FACE ─────────────────────────────── */}
        <div
          className="absolute inset-0 rounded-lg p-4 flex flex-col overflow-y-auto backface-hidden"
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            background: `linear-gradient(135deg, #0f3460 0%, #16213e 100%)`,
            borderLeft: `3px solid ${color}`,
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-display text-accent text-base">
              {spell.name}
            </h3>
            <RotateCcw size={14} className="text-text-muted" />
          </div>

          {/* Full description */}
          <p className="text-text-primary text-sm leading-relaxed whitespace-pre-wrap">
            {spell.description}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
