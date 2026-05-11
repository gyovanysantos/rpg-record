import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import {
  ArrowLeft,
  Shield,
  Wind,
  Eye,
  Loader2,
  Lock,
  Unlock,
  Sparkles,
  Star,
  Swords,
  ScrollText,
  Plus,
  Trash2,
  Flame,
} from "lucide-react";
import {
  useCharacter,
  useUpdateCharacter,
  type CharacterFull,
} from "../hooks/useCharacters";
import {
  useAncestries,
  useExpertPaths,
  useMasterPaths,
} from "../hooks/useGameData";
import SpellCard from "../components/cards/SpellCard";
import InvocationCard from "../components/cards/InvocationCard";
import SpellPickerModal from "../components/modals/SpellPickerModal";
import InvocationEditorModal from "../components/modals/InvocationEditorModal";
import type { Spell, CharacterSpell } from "../hooks/useSpells";
import type { Invocation } from "../hooks/useCreatures";

type TabKey = "stats" | "spells" | "talents" | "invocations" | "equipment" | "notes";

/* ── Talent / Equipment interfaces ── */
interface Talent {
  name: string;
  description: string;
  level: number;
}

interface EquipmentItem {
  name: string;
  category: string;
  equipped: boolean;
  description: string;
}

export default function CharacterSheetPage() {
  const { filename } = useParams<{ filename: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { data: loaded, isLoading, error } = useCharacter(filename ?? null);
  const updateMut = useUpdateCharacter();
  const { data: ancestries } = useAncestries();
  const { data: expertPaths } = useExpertPaths();
  const { data: masterPaths } = useMasterPaths();

  const [char, setChar] = useState<CharacterFull | null>(null);
  const [locked, setLocked] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("stats");
  const [spellPickerOpen, setSpellPickerOpen] = useState(false);
  const [invocationEditorOpen, setInvocationEditorOpen] = useState(false);
  const [editingInvocationIndex, setEditingInvocationIndex] = useState<number | null>(null);
  const [combatMode, setCombatMode] = useState(false);
  const [combatSnapshot, setCombatSnapshot] = useState<CharacterFull | null>(null);
  const [combatStartTime, setCombatStartTime] = useState<Date | null>(null);
  const [showCombatConfirm, setShowCombatConfirm] = useState(false);
  const [combatRound, setCombatRound] = useState(1);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync loaded data into local state
  useEffect(() => {
    if (loaded) setChar({ ...loaded });
  }, [loaded]);

  // Auto-save: debounce 600ms after any change
  const autoSave = useCallback(
    (updated: CharacterFull) => {
      if (!filename) return;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => {
        const {
          health, health_current, defense, perception,
          healing_rate, is_injured, is_incapacitated,
          ...rest
        } = updated;
        void health; void health_current; void defense;
        void perception; void healing_rate; void is_injured;
        void is_incapacitated;
        updateMut.mutate({ filename, data: rest });
      }, 600);
    },
    [filename, updateMut]
  );

  useEffect(() => () => { if (saveTimer.current) clearTimeout(saveTimer.current); }, []);

  const update = useCallback(
    (patch: Partial<CharacterFull>) => {
      setChar((prev) => {
        if (!prev) return prev;
        const next = { ...prev, ...patch };
        autoSave(next);
        return next;
      });
    },
    [autoSave]
  );

  const onAncestryChange = useCallback(
    (name: string) => {
      const a = ancestries?.find((x) => x.name === name);
      const patch: Partial<CharacterFull> = { ancestry: name };
      if (a) {
        patch.size = a.size;
        patch.speed_base = a.speed;
      }
      update(patch);
    },
    [ancestries, update]
  );

  /* ── Spell helpers ── */
  const charSpells = (char?.spells ?? []) as unknown as CharacterSpell[];
  const existingSpellNames = new Set(charSpells.map((s) => s.name));

  const handleAddSpells = useCallback(
    (spells: Spell[]) => {
      if (!char) return;
      const newSpells: CharacterSpell[] = spells.map((s) => ({
        ...s,
        max_castings: 1,
        current_castings: 1,
      }));
      const merged = [...charSpells, ...newSpells];
      update({ spells: merged as unknown as Record<string, unknown>[] });
    },
    [char, charSpells, update]
  );

  const handleRemoveSpell = useCallback(
    (name: string) => {
      const filtered = charSpells.filter((s) => s.name !== name);
      update({ spells: filtered as unknown as Record<string, unknown>[] });
    },
    [charSpells, update]
  );

  const handleCastSpell = useCallback(
    (name: string) => {
      const updated = charSpells.map((s) =>
        s.name === name && s.current_castings > 0
          ? { ...s, current_castings: s.current_castings - 1 }
          : s
      );
      update({ spells: updated as unknown as Record<string, unknown>[] });
    },
    [charSpells, update]
  );

  /* ── Talent helpers ── */
  const talents = (char?.talents ?? []) as unknown as Talent[];

  const handleAddTalent = useCallback(() => {
    const newTalent: Talent = { name: "", description: "", level: 0 };
    update({ talents: [...talents, newTalent] as unknown as Record<string, unknown>[] });
  }, [talents, update]);

  const handleUpdateTalent = useCallback(
    (index: number, patch: Partial<Talent>) => {
      const updated = talents.map((tal, i) => (i === index ? { ...tal, ...patch } : tal));
      update({ talents: updated as unknown as Record<string, unknown>[] });
    },
    [talents, update]
  );

  const handleRemoveTalent = useCallback(
    (index: number) => {
      const filtered = talents.filter((_, i) => i !== index);
      update({ talents: filtered as unknown as Record<string, unknown>[] });
    },
    [talents, update]
  );

  /* ── Equipment helpers ── */
  const equipmentList = (char?.equipment ?? []) as unknown as EquipmentItem[];

  const handleAddEquipment = useCallback(() => {
    const newItem: EquipmentItem = { name: "", category: "", equipped: false, description: "" };
    update({ equipment: [...equipmentList, newItem] as unknown as Record<string, unknown>[] });
  }, [equipmentList, update]);

  const handleUpdateEquipment = useCallback(
    (index: number, patch: Partial<EquipmentItem>) => {
      const updated = equipmentList.map((e, i) => (i === index ? { ...e, ...patch } : e));
      update({ equipment: updated as unknown as Record<string, unknown>[] });
    },
    [equipmentList, update]
  );

  const handleRemoveEquipment = useCallback(
    (index: number) => {
      const filtered = equipmentList.filter((_, i) => i !== index);
      update({ equipment: filtered as unknown as Record<string, unknown>[] });
    },
    [equipmentList, update]
  );

  /* ── Invocation helpers ── */
  const invocations = (char?.invocations ?? []) as unknown as Invocation[];

  const handleAddInvocation = useCallback(
    (inv: Invocation) => {
      update({ invocations: [...invocations, inv] as unknown as Record<string, unknown>[] });
    },
    [invocations, update]
  );

  const handleUpdateInvocation = useCallback(
    (index: number, inv: Invocation) => {
      const updated = invocations.map((item, i) => (i === index ? inv : item));
      update({ invocations: updated as unknown as Record<string, unknown>[] });
    },
    [invocations, update]
  );

  const handleRemoveInvocation = useCallback(
    (index: number) => {
      const filtered = invocations.filter((_, i) => i !== index);
      update({ invocations: filtered as unknown as Record<string, unknown>[] });
    },
    [invocations, update]
  );

  const handleSaveInvocation = useCallback(
    (inv: Invocation) => {
      if (editingInvocationIndex !== null) {
        handleUpdateInvocation(editingInvocationIndex, inv);
      } else {
        handleAddInvocation(inv);
      }
      setEditingInvocationIndex(null);
    },
    [editingInvocationIndex, handleUpdateInvocation, handleAddInvocation]
  );

  const handleEditInvocation = useCallback((index: number) => {
    setEditingInvocationIndex(index);
    setInvocationEditorOpen(true);
  }, []);

  /* ── Combat Mode helpers ── */
  const handleEnterCombat = useCallback(() => {
    if (!char) return;
    // Deep clone the current character state as snapshot
    setCombatSnapshot(JSON.parse(JSON.stringify(char)));
    setCombatStartTime(new Date());
    setCombatMode(true);
    setCombatRound(1);
    setLocked(false); // Force unlock during combat
  }, [char]);

  const buildCombatLog = useCallback((): string => {
    if (!combatSnapshot || !char) return "";
    const now = new Date();
    const dateStr = now.toLocaleDateString("pt-BR") + " " + now.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    const lines: string[] = [];
    lines.push(`${t("combat.logHeader")} (${dateStr}) ---`);

    // Damage taken during combat
    const dmgDelta = char.damage_taken - combatSnapshot.damage_taken;
    if (dmgDelta > 0) lines.push(`${t("combat.logDamage")}: ${dmgDelta}`);

    // Spells cast
    const snapSpells = combatSnapshot.spells as unknown as CharacterSpell[];
    const curSpells = char.spells as unknown as CharacterSpell[];
    const castList: string[] = [];
    for (const snap of snapSpells) {
      const cur = curSpells.find((s) => s.name === snap.name);
      if (cur) {
        const used = snap.current_castings - cur.current_castings;
        if (used > 0) castList.push(`${snap.name} (${used}x)`);
      }
    }
    if (castList.length > 0) lines.push(`${t("combat.logSpellsCast")}: ${castList.join(", ")}`);

    // Fortune used
    if (combatSnapshot.fortune && !char.fortune) lines.push(t("combat.logFortuneUsed"));

    // Gold spent
    const goldDelta = combatSnapshot.gold - char.gold;
    if (goldDelta > 0) lines.push(`${t("combat.logGoldSpent")}: ${goldDelta}`);

    // Corruption gained
    const corrDelta = char.corruption - combatSnapshot.corruption;
    if (corrDelta > 0) lines.push(`${t("combat.logCorruption")}: +${corrDelta}`);

    // Insanity gained
    const insDelta = char.insanity - combatSnapshot.insanity;
    if (insDelta > 0) lines.push(`${t("combat.logInsanity")}: +${insDelta}`);

    // Rounds
    if (combatRound > 0) lines.push(`${t("combat.logRounds")}: ${combatRound}`);

    // Duration
    if (combatStartTime) {
      const mins = Math.round((now.getTime() - combatStartTime.getTime()) / 60000);
      lines.push(`Duração: ~${mins} min`);
    }

    return lines.join("\n");
  }, [char, combatSnapshot, combatStartTime, combatRound, t]);

  const handleExitCombat = useCallback(() => {
    if (!combatSnapshot || !char) return;
    // Build the combat log
    const log = buildCombatLog();
    // Restore snapshot with the combat log appended to notes
    const existingNotes = char.notes || "";
    const separator = existingNotes.trim() ? "\n\n" : "";
    const restoredChar: CharacterFull = {
      ...combatSnapshot,
      notes: existingNotes + separator + log,
    };
    // Update local state and trigger auto-save with restored data
    setChar(restoredChar);
    autoSave(restoredChar);
    // Clean up combat state
    setCombatMode(false);
    setCombatSnapshot(null);
    setCombatStartTime(null);
    setShowCombatConfirm(false);
    setCombatRound(1);
    setLocked(true);
  }, [char, combatSnapshot, buildCombatLog, autoSave]);

  /* ── Loading / Error states ── */
  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 size={36} className="animate-spin text-accent" />
      </div>
    );
  }

  if (error || !char) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate("/characters")} className="btn-ghost flex items-center gap-2">
          <ArrowLeft size={16} /> {t("common.back")}
        </button>
        <div className="bg-danger/20 border border-danger text-danger rounded-lg p-4">
          {t("characters.loadError")}
        </div>
      </div>
    );
  }

  /* ── Computed values ── */
  const strMod = char.strength - 10;
  const agiMod = char.agility - 10;
  const intMod = char.intellect - 10;
  const wilMod = char.will - 10;
  const health = char.strength + char.health_bonus;
  const healingRate = Math.max(1, Math.floor(health / 4) + char.healing_rate_bonus);
  const defense = char.agility + char.defense_bonus;
  const perception = intMod + char.perception_bonus;
  const healthCurrent = Math.max(0, health - char.damage_taken);
  const isInjured = char.damage_taken >= Math.floor(health / 2);
  const isIncapacitated = char.damage_taken >= health;
  const healthPct = health > 0 ? (healthCurrent / health) * 100 : 0;

  /* ── Tab definitions ── */
  const tabs: { key: TabKey; label: string; icon: React.ReactNode; count?: number }[] = [
    { key: "stats", label: t("characters.stats", "Stats"), icon: <Shield size={16} /> },
    { key: "spells", label: t("spells.title"), icon: <Sparkles size={16} />, count: charSpells.length },
    { key: "talents", label: t("talents.title"), icon: <Star size={16} />, count: talents.length },
    { key: "invocations", label: t("invocations.title"), icon: <Flame size={16} />, count: invocations.length },
    { key: "equipment", label: t("characters.equipment"), icon: <Swords size={16} />, count: equipmentList.length },
    { key: "notes", label: t("characters.notes"), icon: <ScrollText size={16} /> },
  ];

  return (
    <div className={`space-y-4 pb-8 ${combatMode ? "ring-2 ring-danger/50 rounded-xl p-3" : ""}`}>
      {/* ── Combat Active Banner ── */}
      {combatMode && (
        <div className="bg-danger/15 border border-danger/40 rounded-lg p-3 flex items-center gap-3 animate-pulse-slow">
          <Swords size={20} className="text-danger shrink-0" />
          <div className="flex-1">
            <span className="text-danger font-display font-bold">{t("combat.active")}</span>
            <p className="text-text-muted text-sm">{t("combat.activeSub")}</p>
          </div>
          {/* ── Round Tracker ── */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setCombatRound((r) => Math.max(1, r - 1))}
              disabled={combatRound <= 1}
              className="w-7 h-7 rounded-md border border-danger/40 text-danger hover:bg-danger/20 transition-colors flex items-center justify-center text-sm font-bold disabled:opacity-30 disabled:cursor-not-allowed"
            >
              −
            </button>
            <div className="text-center min-w-[4rem]">
              <span className="text-danger font-display font-bold text-lg leading-none">{combatRound}</span>
              <p className="text-text-muted text-[0.65rem] leading-none mt-0.5">{t("combat.round")}</p>
            </div>
            <button
              onClick={() => setCombatRound((r) => r + 1)}
              className="w-7 h-7 rounded-md border border-danger/40 text-danger hover:bg-danger/20 transition-colors flex items-center justify-center text-sm font-bold"
            >
              +
            </button>
          </div>
        </div>
      )}

      {/* ── Combat End Confirmation Dialog ── */}
      {showCombatConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-surface border border-border rounded-xl p-6 max-w-md w-full mx-4 space-y-4 shadow-xl">
            <h3 className="text-lg font-display text-accent">{t("combat.confirmTitle")}</h3>
            <p className="text-text-muted text-sm">{t("combat.confirmMessage")}</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCombatConfirm(false)}
                className="px-4 py-2 rounded-lg border border-border text-text-muted hover:text-text-primary transition-colors text-sm"
              >
                {t("combat.confirmCancel")}
              </button>
              <button
                onClick={handleExitCombat}
                className="px-4 py-2 rounded-lg bg-danger text-white hover:bg-danger/80 transition-colors text-sm font-medium"
              >
                {t("combat.confirmYes")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Top bar ── */}
      <div className="flex items-center gap-4 flex-wrap">
        <button
          onClick={() => {
            if (combatMode) {
              if (window.confirm(t("combat.navWarning"))) {
                setCombatMode(false);
                setCombatSnapshot(null);
                setCombatStartTime(null);
                navigate("/characters");
              }
            } else {
              navigate("/characters");
            }
          }}
          className="btn-ghost flex items-center gap-2"
        >
          <ArrowLeft size={16} /> {t("common.back")}
        </button>

        <div className="flex-1">
          <span className="text-lg font-display text-accent">{char.name}</span>
          <span className="text-text-muted ml-2 text-sm">
            {t("characters.level")} {char.level} · {char.ancestry}
          </span>
        </div>

        {/* Combat Mode Toggle */}
        <button
          onClick={() => {
            if (combatMode) {
              setShowCombatConfirm(true);
            } else {
              handleEnterCombat();
            }
          }}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors text-sm font-medium ${
            combatMode
              ? "border-danger text-danger bg-danger/10 hover:bg-danger/20"
              : "border-border text-text-muted hover:text-danger hover:border-danger"
          }`}
        >
          <Swords size={14} />
          {combatMode ? t("combat.exit") : t("combat.enter")}
        </button>

        {/* Lock/Unlock — disabled during combat */}
        <button
          onClick={() => !combatMode && setLocked(!locked)}
          disabled={combatMode}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors text-sm ${
            combatMode
              ? "border-border text-text-muted/40 cursor-not-allowed"
              : locked
                ? "border-border text-text-muted hover:text-accent hover:border-accent"
                : "border-accent text-accent bg-accent/10"
          }`}
        >
          {locked && !combatMode ? <Lock size={14} /> : <Unlock size={14} />}
          {locked && !combatMode ? t("characters.editStats") : t("characters.lockStats")}
        </button>

        {updateMut.isPending && (
          <span className="text-sm text-text-muted flex items-center gap-1">
            <Loader2 size={14} className="animate-spin" /> {t("common.saving")}
          </span>
        )}
      </div>

      {/* ── Tab bar ── */}
      <div className="flex gap-1 border-b border-border overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors
              border-b-2 whitespace-nowrap ${
                activeTab === tab.key
                  ? "border-accent text-accent"
                  : "border-transparent text-text-muted hover:text-text-primary hover:border-border"
              }`}
          >
            {tab.icon}
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="bg-accent/20 text-accent text-sm px-1.5 py-0.5 rounded-full min-w-[1.5rem] text-center">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      {activeTab === "stats" && (
        <StatsTab
          char={char}
          locked={combatMode ? false : locked}
          update={update}
          onAncestryChange={onAncestryChange}
          ancestries={ancestries}
          expertPaths={expertPaths}
          masterPaths={masterPaths}
          strMod={strMod} agiMod={agiMod} intMod={intMod} wilMod={wilMod}
          health={health} healthCurrent={healthCurrent} healthPct={healthPct}
          healingRate={healingRate} defense={defense} perception={perception}
          isInjured={isInjured} isIncapacitated={isIncapacitated}
          t={t}
        />
      )}

      {activeTab === "spells" && (
        <SpellsTab
          spells={charSpells}
          onAdd={() => setSpellPickerOpen(true)}
          onRemove={handleRemoveSpell}
          onCast={handleCastSpell}
          t={t}
        />
      )}

      {activeTab === "talents" && (
        <TalentsTab
          talents={talents}
          onAdd={handleAddTalent}
          onUpdate={handleUpdateTalent}
          onRemove={handleRemoveTalent}
          t={t}
        />
      )}

      {activeTab === "invocations" && (
        <InvocationsTab
          invocations={invocations}
          onAdd={() => {
            setEditingInvocationIndex(null);
            setInvocationEditorOpen(true);
          }}
          onEdit={handleEditInvocation}
          onRemove={handleRemoveInvocation}
          t={t}
        />
      )}

      {activeTab === "equipment" && (
        <EquipmentTab
          equipment={equipmentList}
          onAdd={handleAddEquipment}
          onUpdate={handleUpdateEquipment}
          onRemove={handleRemoveEquipment}
          t={t}
        />
      )}

      {activeTab === "notes" && (
        <div className="card">
          <textarea
            value={char.notes}
            onChange={(e) => update({ notes: e.target.value })}
            rows={12}
            className="input-field resize-y"
            placeholder={t("characters.notesPlaceholder")}
          />
        </div>
      )}

      {/* Spell Picker Modal */}
      <SpellPickerModal
        open={spellPickerOpen}
        onClose={() => setSpellPickerOpen(false)}
        onConfirm={handleAddSpells}
        existingNames={existingSpellNames}
      />

      {/* Invocation Editor Modal */}
      <InvocationEditorModal
        open={invocationEditorOpen}
        onClose={() => {
          setInvocationEditorOpen(false);
          setEditingInvocationIndex(null);
        }}
        onSave={handleSaveInvocation}
        initial={editingInvocationIndex !== null ? invocations[editingInvocationIndex] : null}
      />
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   STATS TAB — Identity, Attributes, Health, Combat, Secondary
   ════════════════════════════════════════════════════════════════ */

function StatsTab({
  char, locked, update, onAncestryChange,
  ancestries, expertPaths, masterPaths,
  strMod, agiMod, intMod, wilMod,
  health, healthCurrent, healthPct, healingRate,
  defense, perception, isInjured, isIncapacitated,
  t,
}: {
  char: CharacterFull;
  locked: boolean;
  update: (patch: Partial<CharacterFull>) => void;
  onAncestryChange: (name: string) => void;
  ancestries: { name: string; size: string; speed: number }[] | undefined;
  expertPaths: string[] | undefined;
  masterPaths: string[] | undefined;
  strMod: number; agiMod: number; intMod: number; wilMod: number;
  health: number; healthCurrent: number; healthPct: number;
  healingRate: number; defense: number; perception: number;
  isInjured: boolean; isIncapacitated: boolean;
  t: TFunction;
}) {
  return (
    <div className="space-y-6">
      {/* Identity */}
      <div className="card">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label={t("characters.name")}>
            <input type="text" value={char.name} onChange={(e) => update({ name: e.target.value })} disabled={locked} className="input-field" />
          </Field>
          <Field label={t("characters.level")}>
            <NumberInput value={char.level} min={0} max={10} disabled={locked} onChange={(v) => update({ level: v })} />
          </Field>
          <Field label={t("characters.ancestry")}>
            <select value={char.ancestry} onChange={(e) => onAncestryChange(e.target.value)} disabled={locked} className="input-field">
              {ancestries?.map((a) => <option key={a.name} value={a.name}>{a.name}</option>)}
              {ancestries && !ancestries.find((a) => a.name === char.ancestry) && <option value={char.ancestry}>{char.ancestry}</option>}
            </select>
          </Field>
          <Field label={t("characters.size")}>
            <input type="text" value={char.size} onChange={(e) => update({ size: e.target.value })} disabled={locked} className="input-field" />
          </Field>
          <Field label={t("characters.novicePath")}>
            <input type="text" value={char.novice_path} onChange={(e) => update({ novice_path: e.target.value })} disabled={locked} className="input-field" placeholder="—" />
          </Field>
          <Field label={t("characters.expertPath")}>
            <ComboSelect value={char.expert_path} options={expertPaths ?? []} disabled={locked} onChange={(v) => update({ expert_path: v })} id="expertPath" />
          </Field>
          <Field label={t("characters.masterPath")}>
            <ComboSelect value={char.master_path} options={masterPaths ?? []} disabled={locked} onChange={(v) => update({ master_path: v })} id="masterPath" />
          </Field>
        </div>
      </div>

      {/* Attributes */}
      <div className="card">
        <h2 className="text-lg font-display text-accent mb-4">{t("characters.attributes")}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <AttrBlock label={t("characters.strength")} value={char.strength} mod={strMod} disabled={locked} onChange={(v) => update({ strength: v })} />
          <AttrBlock label={t("characters.agility")} value={char.agility} mod={agiMod} disabled={locked} onChange={(v) => update({ agility: v })} />
          <AttrBlock label={t("characters.intellect")} value={char.intellect} mod={intMod} disabled={locked} onChange={(v) => update({ intellect: v })} />
          <AttrBlock label={t("characters.will")} value={char.will} mod={wilMod} disabled={locked} onChange={(v) => update({ will: v })} />
        </div>
      </div>

      {/* Health bar */}
      <div className="card">
        <h2 className="text-lg font-display text-accent mb-4">{t("characters.health")}</h2>
        <div className="mb-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-text-muted">{healthCurrent} / {health}</span>
            <span className={`font-semibold ${isIncapacitated ? "text-danger" : isInjured ? "text-accent" : "text-success"}`}>
              {isIncapacitated ? t("characters.incapacitated") : isInjured ? t("characters.injured") : t("characters.healthy")}
            </span>
          </div>
          <div className="w-full h-4 bg-background rounded-full overflow-hidden border border-border">
            <div className={`h-full transition-all duration-300 rounded-full ${isIncapacitated ? "bg-danger" : isInjured ? "bg-accent" : "bg-success"}`} style={{ width: `${healthPct}%` }} />
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Field label={t("characters.damageTaken")}><NumberInput value={char.damage_taken} min={0} max={999} disabled={locked} onChange={(v) => update({ damage_taken: v })} /></Field>
          <Field label={t("characters.healthBonus")}><NumberInput value={char.health_bonus} min={-50} max={50} disabled={locked} onChange={(v) => update({ health_bonus: v })} /></Field>
          <Field label={t("characters.healingRate")}><div className="input-field bg-background/50 cursor-default">{healingRate}</div></Field>
          <Field label={t("characters.healingRateBonus")}><NumberInput value={char.healing_rate_bonus} min={-20} max={50} disabled={locked} onChange={(v) => update({ healing_rate_bonus: v })} /></Field>
        </div>
      </div>

      {/* Combat */}
      <div className="card">
        <h2 className="text-lg font-display text-accent mb-4">{t("characters.combat")}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatDisplay icon={<Shield size={18} />} label={t("characters.defense")} value={defense} />
          <Field label={t("characters.defenseBonus")}><NumberInput value={char.defense_bonus} min={-20} max={30} disabled={locked} onChange={(v) => update({ defense_bonus: v })} /></Field>
          <StatDisplay icon={<Wind size={18} />} label={t("characters.speed")} value={char.speed_base} />
          <Field label={t("characters.speed")}><NumberInput value={char.speed_base} min={0} max={30} disabled={locked} onChange={(v) => update({ speed_base: v })} /></Field>
          <StatDisplay icon={<Eye size={18} />} label={t("characters.perception")} value={perception} />
          <Field label={t("characters.perceptionBonus")}><NumberInput value={char.perception_bonus} min={-10} max={20} disabled={locked} onChange={(v) => update({ perception_bonus: v })} /></Field>
        </div>
      </div>

      {/* Secondary */}
      <div className="card">
        <h2 className="text-lg font-display text-accent mb-4">{t("characters.secondary")}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Field label={t("characters.power")}><NumberInput value={char.power} min={0} max={10} disabled={locked} onChange={(v) => update({ power: v })} /></Field>
          <Field label={t("characters.corruption")}><NumberInput value={char.corruption} min={0} max={20} disabled={locked} onChange={(v) => update({ corruption: v })} /></Field>
          <Field label={t("characters.insanity")}><NumberInput value={char.insanity} min={0} max={20} disabled={locked} onChange={(v) => update({ insanity: v })} /></Field>
          <Field label={t("characters.fortune")}>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={char.fortune} onChange={(e) => update({ fortune: e.target.checked })} disabled={locked} className="w-5 h-5 rounded accent-accent" />
              <span className={`text-sm ${char.fortune ? "text-success" : "text-danger"}`}>{char.fortune ? "✓" : "✗"}</span>
            </label>
          </Field>
          <Field label={t("characters.gold")}><NumberInput value={char.gold} min={0} max={99999} disabled={locked} onChange={(v) => update({ gold: v })} /></Field>
        </div>
      </div>

      {/* Languages & Professions */}
      <div className="card">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label={t("characters.languages")}>
            <input type="text" value={char.languages.join(", ")} onChange={(e) => update({ languages: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} disabled={locked} className="input-field" placeholder="Common, Elvish..." />
          </Field>
          <Field label={t("characters.professions")}>
            <input type="text" value={char.professions.join(", ")} onChange={(e) => update({ professions: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} disabled={locked} className="input-field" placeholder="—" />
          </Field>
        </div>
      </div>
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   SPELLS TAB — My Spell Deck + Add from picker + Cast/Remove
   ════════════════════════════════════════════════════════════════ */

function SpellsTab({
  spells,
  onAdd,
  onRemove,
  onCast,
  t,
}: {
  spells: CharacterSpell[];
  onAdd: () => void;
  onRemove: (name: string) => void;
  onCast: (name: string) => void;
  t: TFunction;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-text-muted text-sm">
          {spells.length === 0
            ? t("spells.noSpells", "Nenhuma magia no grimório. Adicione magias do banco de dados.")
            : `${spells.length} ${spells.length === 1 ? t("spells.spellSingular", "magia") : t("spells.spellPlural", "magias")} ${t("spells.inDeck", "no grimório")}`}
        </p>
        <button onClick={onAdd} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> {t("spells.addSpell")}
        </button>
      </div>

      {spells.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {spells.map((spell) => (
            <div key={spell.name} className="relative group">
              <SpellCard
                spell={spell}
                interactive
                onCast={() => onCast(spell.name)}
              />
              {/* Remove button */}
              <button
                onClick={() => onRemove(spell.name)}
                className="absolute top-2 right-2 p-1.5 rounded-lg bg-danger/80 text-white
                           opacity-0 group-hover:opacity-100 transition-opacity hover:bg-danger z-10"
                title={t("spells.removeSpell")}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   TALENTS TAB — Editable list of talents (name, level, description)
   ════════════════════════════════════════════════════════════════ */

function TalentsTab({
  talents,
  onAdd,
  onUpdate,
  onRemove,
  t,
}: {
  talents: Talent[];
  onAdd: () => void;
  onUpdate: (index: number, patch: Partial<Talent>) => void;
  onRemove: (index: number) => void;
  t: TFunction;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-text-muted text-sm">
          {talents.length === 0
            ? t("talents.noTalents")
            : `${talents.length} ${talents.length === 1 ? t("talents.talentSingular", "talento") : t("talents.talentPlural", "talentos")}`}
        </p>
        <button onClick={onAdd} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> {t("talents.addTalent")}
        </button>
      </div>

      {talents.map((talent, i) => (
        <div key={i} className="card">
          <div className="flex gap-3 items-start">
            <div className="flex-1 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                <input
                  type="text"
                  value={talent.name}
                  onChange={(e) => onUpdate(i, { name: e.target.value })}
                  className="input-field"
                  placeholder={t("talents.talentName", "Nome do talento")}
                />
                <div className="flex items-center gap-2">
                  <label className="text-text-muted text-sm whitespace-nowrap">{t("characters.level")}:</label>
                  <input
                    type="number"
                    value={talent.level}
                    min={0}
                    max={10}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10);
                      if (!isNaN(v)) onUpdate(i, { level: Math.max(0, Math.min(10, v)) });
                    }}
                    className="input-field text-center w-16"
                  />
                </div>
              </div>
              <textarea
                value={talent.description}
                onChange={(e) => onUpdate(i, { description: e.target.value })}
                rows={2}
                className="input-field resize-y"
                placeholder={t("talents.talentDescription", "Descrição...")}
              />
            </div>
            <button
              onClick={() => onRemove(i)}
              className="p-2 text-text-muted hover:text-danger transition-colors rounded-lg hover:bg-danger/10"
              title={t("common.delete")}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   EQUIPMENT TAB — Editable list (name, category, equipped, description)
   ════════════════════════════════════════════════════════════════ */

function EquipmentTab({
  equipment,
  onAdd,
  onUpdate,
  onRemove,
  t,
}: {
  equipment: EquipmentItem[];
  onAdd: () => void;
  onUpdate: (index: number, patch: Partial<EquipmentItem>) => void;
  onRemove: (index: number) => void;
  t: TFunction;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-text-muted text-sm">
          {equipment.length === 0
            ? t("characters.noEquipment", "Nenhum equipamento. Adicione itens.")
            : `${equipment.length} ${equipment.length === 1 ? t("characters.itemSingular", "item") : t("characters.itemPlural", "itens")}`}
        </p>
        <button onClick={onAdd} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> {t("characters.addEquipment", "Adicionar Item")}
        </button>
      </div>

      {equipment.map((item, i) => (
        <div key={i} className="card">
          <div className="flex gap-3 items-start">
            <div className="flex-1 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3 items-center">
                <input
                  type="text"
                  value={item.name}
                  onChange={(e) => onUpdate(i, { name: e.target.value })}
                  className="input-field"
                  placeholder={t("characters.itemName", "Nome do item")}
                />
                <input
                  type="text"
                  value={item.category}
                  onChange={(e) => onUpdate(i, { category: e.target.value })}
                  className="input-field w-32"
                  placeholder={t("characters.category", "Categoria")}
                />
                <label className="flex items-center gap-2 cursor-pointer whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={item.equipped}
                    onChange={(e) => onUpdate(i, { equipped: e.target.checked })}
                    className="w-4 h-4 rounded accent-accent"
                  />
                  <span className="text-sm text-text-muted">{t("characters.equipped", "Equipado")}</span>
                </label>
              </div>
              <textarea
                value={item.description}
                onChange={(e) => onUpdate(i, { description: e.target.value })}
                rows={2}
                className="input-field resize-y"
                placeholder={t("characters.itemDescription", "Descrição...")}
              />
            </div>
            <button
              onClick={() => onRemove(i)}
              className="p-2 text-text-muted hover:text-danger transition-colors rounded-lg hover:bg-danger/10"
              title={t("common.delete")}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   INVOCATIONS TAB — Card-style grid of summoned creatures
   ════════════════════════════════════════════════════════════════ */

function InvocationsTab({
  invocations,
  onAdd,
  onEdit,
  onRemove,
  t,
}: {
  invocations: Invocation[];
  onAdd: () => void;
  onEdit: (index: number) => void;
  onRemove: (index: number) => void;
  t: TFunction;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-text-muted text-sm">
          {invocations.length === 0
            ? t("invocations.noInvocations")
            : `${invocations.length} ${invocations.length === 1 ? t("invocations.invocationSingular") : t("invocations.invocationPlural")}`}
        </p>
        <button onClick={onAdd} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> {t("invocations.addInvocation")}
        </button>
      </div>

      {invocations.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {invocations.map((inv, i) => (
            <InvocationCard
              key={`${inv.name}-${i}`}
              invocation={inv}
              onEdit={() => onEdit(i)}
              onDelete={() => onRemove(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
}


/* ════════════════════════════════════════════════════════════════
   SMALL REUSABLE COMPONENTS
   ════════════════════════════════════════════════════════════════ */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-text-muted mb-1">{label}</label>
      {children}
    </div>
  );
}

function NumberInput({
  value, min, max, disabled, onChange,
}: {
  value: number; min: number; max: number; disabled: boolean;
  onChange: (v: number) => void;
}) {
  return (
    <input
      type="number"
      value={value}
      min={min}
      max={max}
      disabled={disabled}
      onChange={(e) => {
        const v = parseInt(e.target.value, 10);
        if (!isNaN(v)) onChange(Math.max(min, Math.min(max, v)));
      }}
      className="input-field text-center w-full"
    />
  );
}

function AttrBlock({
  label, value, mod, disabled, onChange,
}: {
  label: string; value: number; mod: number; disabled: boolean;
  onChange: (v: number) => void;
}) {
  return (
    <div className="bg-surface border border-border rounded-lg p-3 text-center">
      <div className="text-sm text-text-muted mb-1">{label}</div>
      <input
        type="number" value={value} min={1} max={30} disabled={disabled}
        onChange={(e) => {
          const v = parseInt(e.target.value, 10);
          if (!isNaN(v)) onChange(Math.max(1, Math.min(30, v)));
        }}
        className="input-field text-center text-2xl font-bold w-full mb-1"
      />
      <div className={`text-sm font-medium ${mod >= 0 ? "text-success" : "text-danger"}`}>
        ({mod >= 0 ? "+" : ""}{mod})
      </div>
    </div>
  );
}

function StatDisplay({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-3 text-center">
      <div className="text-accent mb-1 flex justify-center">{icon}</div>
      <div className="text-2xl font-bold text-text-primary">{value}</div>
      <div className="text-sm text-text-muted">{label}</div>
    </div>
  );
}

function ComboSelect({
  value, options, disabled, onChange, id,
}: {
  value: string; options: string[]; disabled: boolean;
  onChange: (v: string) => void; id: string;
}) {
  const listId = `combo-${id}`;
  return (
    <div className="relative">
      <input
        type="text" list={listId} value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled} className="input-field w-full" placeholder="—"
      />
      <datalist id={listId}>
        {options.map((o) => <option key={o} value={o} />)}
      </datalist>
    </div>
  );
}
