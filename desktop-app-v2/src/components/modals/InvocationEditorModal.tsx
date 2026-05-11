/**
 * InvocationEditorModal — Modal for creating/editing an invocation (creature stat block).
 *
 * Features:
 * - Template selector dropdown (populate from creatures.json)
 * - All creature stat fields: name, difficulty, type, size, stats, traits, attacks, description
 * - Pre-fills from selected template, or blank for manual entry
 */
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { X, Search } from "lucide-react";
import { useCreatures, type Invocation } from "../../hooks/useCreatures";

interface InvocationEditorModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (invocation: Invocation) => void;
  /** If provided, we're editing an existing invocation. */
  initial?: Invocation | null;
}

const BLANK_INVOCATION: Invocation = {
  name: "",
  difficulty: 0,
  creature_type: "",
  size: "1",
  perception: 10,
  defense: 10,
  health: 10,
  strength: 10,
  agility: 10,
  intellect: 10,
  will: 10,
  speed: 10,
  traits: "",
  immunities: "",
  attack_options: "",
  special_attacks: "",
  description: "",
};

export default function InvocationEditorModal({
  open,
  onClose,
  onSave,
  initial,
}: InvocationEditorModalProps) {
  const { t } = useTranslation();
  const { data: creatures } = useCreatures();
  const [form, setForm] = useState<Invocation>(BLANK_INVOCATION);
  const [templateSearch, setTemplateSearch] = useState("");

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setForm(initial ? { ...initial } : { ...BLANK_INVOCATION });
      setTemplateSearch("");
    }
  }, [open, initial]);

  if (!open) return null;

  const patch = (p: Partial<Invocation>) => setForm((prev) => ({ ...prev, ...p }));
  const numPatch = (key: keyof Invocation, raw: string) => {
    const v = parseInt(raw, 10);
    if (!isNaN(v)) patch({ [key]: v } as Partial<Invocation>);
  };

  const filteredCreatures = (creatures ?? []).filter((c) =>
    c.name.toLowerCase().includes(templateSearch.toLowerCase())
  );

  const handleSelectTemplate = (creature: Invocation) => {
    setForm({ ...creature });
    setTemplateSearch("");
  };

  const handleSave = () => {
    onSave(form);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        className="bg-surface border border-border rounded-xl w-full max-w-2xl mx-4 shadow-xl
                    max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
          <h2 className="text-lg font-display text-accent">
            {initial ? t("invocations.editInvocation") : t("invocations.newInvocation")}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-background transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* ── Template selector ── */}
          {!initial && creatures && creatures.length > 0 && (
            <div>
              <label className="block text-sm text-text-muted mb-1">
                {t("invocations.template")}
              </label>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  value={templateSearch}
                  onChange={(e) => setTemplateSearch(e.target.value)}
                  placeholder={t("invocations.searchTemplate")}
                  className="input-field pl-9 w-full"
                />
              </div>
              {templateSearch && filteredCreatures.length > 0 && (
                <div className="mt-1 bg-background border border-border rounded-lg max-h-40 overflow-y-auto">
                  {filteredCreatures.map((c) => (
                    <button
                      key={c.name}
                      onClick={() => handleSelectTemplate(c)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-surface transition-colors
                                 flex items-center justify-between"
                    >
                      <span className="text-text-primary">{c.name}</span>
                      <span className="text-text-muted text-xs">
                        {t("invocations.difficulty")} {c.difficulty} · {c.creature_type}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Identity ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField label={t("invocations.name")}>
              <input
                type="text"
                value={form.name}
                onChange={(e) => patch({ name: e.target.value })}
                className="input-field"
                placeholder={t("invocations.namePlaceholder")}
              />
            </FormField>
            <FormField label={t("invocations.creatureType")}>
              <input
                type="text"
                value={form.creature_type}
                onChange={(e) => patch({ creature_type: e.target.value })}
                className="input-field"
                placeholder={t("invocations.typePlaceholder")}
              />
            </FormField>
            <FormField label={t("invocations.difficulty")}>
              <input
                type="number"
                value={form.difficulty}
                min={0}
                onChange={(e) => numPatch("difficulty", e.target.value)}
                className="input-field text-center"
              />
            </FormField>
            <FormField label={t("invocations.size")}>
              <input
                type="text"
                value={form.size}
                onChange={(e) => patch({ size: e.target.value })}
                className="input-field text-center"
              />
            </FormField>
          </div>

          {/* ── Core stats ── */}
          <div>
            <h3 className="text-sm text-accent font-semibold uppercase tracking-wider mb-2">
              {t("invocations.coreStats")}
            </h3>
            <div className="grid grid-cols-4 gap-3">
              {(["strength", "agility", "intellect", "will"] as const).map((attr) => (
                <FormField key={attr} label={t(`characters.${attr}`)}>
                  <input
                    type="number"
                    value={form[attr]}
                    min={1}
                    max={30}
                    onChange={(e) => numPatch(attr, e.target.value)}
                    className="input-field text-center"
                  />
                </FormField>
              ))}
            </div>
          </div>

          {/* ── Derived stats ── */}
          <div>
            <h3 className="text-sm text-accent font-semibold uppercase tracking-wider mb-2">
              {t("invocations.derivedStats")}
            </h3>
            <div className="grid grid-cols-4 gap-3">
              <FormField label={t("characters.health")}>
                <input type="number" value={form.health} min={1} onChange={(e) => numPatch("health", e.target.value)} className="input-field text-center" />
              </FormField>
              <FormField label={t("characters.defense")}>
                <input type="number" value={form.defense} min={0} onChange={(e) => numPatch("defense", e.target.value)} className="input-field text-center" />
              </FormField>
              <FormField label={t("characters.perception")}>
                <input type="number" value={form.perception} min={0} onChange={(e) => numPatch("perception", e.target.value)} className="input-field text-center" />
              </FormField>
              <FormField label={t("characters.speed")}>
                <input type="number" value={form.speed} min={0} onChange={(e) => numPatch("speed", e.target.value)} className="input-field text-center" />
              </FormField>
            </div>
          </div>

          {/* ── Text fields ── */}
          <FormField label={t("invocations.attacks")}>
            <textarea
              value={form.attack_options}
              onChange={(e) => patch({ attack_options: e.target.value })}
              rows={2}
              className="input-field resize-y"
              placeholder={t("invocations.attacksPlaceholder")}
            />
          </FormField>

          <FormField label={t("invocations.specialAttacks")}>
            <textarea
              value={form.special_attacks}
              onChange={(e) => patch({ special_attacks: e.target.value })}
              rows={2}
              className="input-field resize-y"
              placeholder={t("invocations.specialAttacksPlaceholder")}
            />
          </FormField>

          <FormField label={t("invocations.traits")}>
            <textarea
              value={form.traits}
              onChange={(e) => patch({ traits: e.target.value })}
              rows={2}
              className="input-field resize-y"
              placeholder={t("invocations.traitsPlaceholder")}
            />
          </FormField>

          <FormField label={t("invocations.immunities")}>
            <input
              type="text"
              value={form.immunities}
              onChange={(e) => patch({ immunities: e.target.value })}
              className="input-field"
              placeholder={t("invocations.immunitiesPlaceholder")}
            />
          </FormField>

          <FormField label={t("invocations.description")}>
            <textarea
              value={form.description}
              onChange={(e) => patch({ description: e.target.value })}
              rows={3}
              className="input-field resize-y"
              placeholder={t("invocations.descriptionPlaceholder")}
            />
          </FormField>
        </div>

        {/* Footer */}
        <div className="flex gap-3 justify-end p-4 border-t border-border shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-border text-text-muted hover:text-text-primary transition-colors text-sm"
          >
            {t("common.cancel")}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-accent text-background hover:bg-accent/80 transition-colors text-sm font-medium"
          >
            {t("common.save")}
          </button>
        </div>
      </div>
    </div>
  );
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-text-muted mb-1">{label}</label>
      {children}
    </div>
  );
}
