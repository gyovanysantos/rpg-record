/**
 * SpellDeck — A filterable grid of SpellCards.
 *
 * Features:
 * - Search input (filters by name)
 * - Tradition dropdown filter
 * - Rank filter buttons
 * - Group by tradition toggle
 * - Responsive grid layout
 */
import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Search, Filter, Layers, LayoutGrid } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useSpells, useTraditions, type Spell } from "../../hooks/useSpells";
import SpellCard from "./SpellCard";
import { getTraditionColor } from "../../utils/traditionColors";

interface SpellDeckProps {
  /** Called when a spell card is clicked (for picker mode) */
  onSelect?: (spell: Spell) => void;
  /** Set of already-selected spell names (for picker highlights) */
  selectedNames?: Set<string>;
}

const RANKS = [0, 1, 2, 3, 4, 5];

export default function SpellDeck({ onSelect, selectedNames }: SpellDeckProps) {
  const { t } = useTranslation();

  // Filter state
  const [search, setSearch] = useState("");
  const [tradition, setTradition] = useState("");
  const [rank, setRank] = useState<number | undefined>(undefined);
  const [groupByTradition, setGroupByTradition] = useState(false);

  // API queries
  const { data: spells = [], isLoading, isError } = useSpells({
    tradition: tradition || undefined,
    rank,
    search: search || undefined,
  });
  const { data: traditions = [] } = useTraditions();

  // Group spells by tradition if toggled
  const grouped = useMemo(() => {
    if (!groupByTradition) return { "": spells };
    const map: Record<string, Spell[]> = {};
    for (const s of spells) {
      if (!map[s.tradition]) map[s.tradition] = [];
      map[s.tradition].push(s);
    }
    return map;
  }, [spells, groupByTradition]);

  return (
    <div className="space-y-4">
      {/* ── FILTER BAR ─────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder={t("spells.searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface border border-border rounded-lg pl-9 pr-4 py-2
                       text-text-primary text-base placeholder:text-text-muted
                       focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        {/* Tradition dropdown */}
        <div className="relative">
          <Filter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          <select
            value={tradition}
            onChange={(e) => setTradition(e.target.value)}
            className="bg-surface border border-border rounded-lg pl-9 pr-8 py-2
                       text-text-primary text-base appearance-none cursor-pointer
                       focus:outline-none focus:border-accent transition-colors"
          >
            <option value="">{t("spells.allTraditions")}</option>
            {traditions.map((trad) => (
              <option key={trad} value={trad}>{trad}</option>
            ))}
          </select>
        </div>

        {/* Rank filter buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setRank(undefined)}
            className={`px-3 py-1.5 text-sm rounded transition-colors
              ${rank === undefined
                ? "bg-accent text-background font-bold"
                : "bg-surface text-text-muted hover:text-text border border-border"
              }`}
          >
            {t("spells.allRanks")}
          </button>
          {RANKS.map((r) => (
            <button
              key={r}
              onClick={() => setRank(rank === r ? undefined : r)}
              className={`px-3 py-1.5 text-sm rounded transition-colors
                ${rank === r
                  ? "bg-accent text-background font-bold"
                  : "bg-surface text-text-muted hover:text-text border border-border"
                }`}
            >
              R{r}
            </button>
          ))}
        </div>

        {/* Group toggle */}
        <button
          onClick={() => setGroupByTradition((v) => !v)}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors
            ${groupByTradition
              ? "bg-accent/20 text-accent border border-accent/40"
              : "bg-surface text-text-muted border border-border hover:text-text"
            }`}
          title={t("spells.groupByTradition")}
        >
          {groupByTradition ? <Layers size={14} /> : <LayoutGrid size={14} />}
          {t("spells.group")}
        </button>
      </div>

      {/* ── RESULTS COUNT ──────────────────────── */}
      <p className="text-text-muted text-sm">
        {t("spells.showing", { count: spells.length })}
      </p>

      {/* ── LOADING / ERROR / EMPTY ────────────── */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-accent border-t-transparent rounded-full" />
        </div>
      )}

      {isError && (
        <div className="card text-danger text-sm">
          {t("common.error")}
        </div>
      )}

      {!isLoading && !isError && spells.length === 0 && (
        <div className="card text-text-muted text-sm text-center py-8">
          {t("spells.noResults")}
        </div>
      )}

      {/* ── SPELL GRID ─────────────────────────── */}
      {!isLoading && !isError && spells.length > 0 && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([groupName, groupSpells]) => (
            <div key={groupName || "__all"}>
              {/* Tradition group header */}
              {groupName && (
                <div className="flex items-center gap-2 mb-3">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getTraditionColor(groupName) }}
                  />
                  <h2 className="font-display text-text text-lg">{groupName}</h2>
                  <span className="text-text-muted text-sm">
                    ({groupSpells.length})
                  </span>
                </div>
              )}

              {/* Cards grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                <AnimatePresence mode="popLayout">
                  {groupSpells.map((spell) => (
                    <motion.div
                      key={`${spell.tradition}-${spell.name}`}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.2 }}
                    >
                      <SpellCard
                        spell={spell}
                        onSelect={onSelect ? () => onSelect(spell) : undefined}
                        selected={selectedNames?.has(spell.name)}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
