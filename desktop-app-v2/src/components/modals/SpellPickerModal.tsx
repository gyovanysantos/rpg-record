/**
 * SpellPickerModal — Modal to browse and pick spells from the database.
 *
 * Left side: SpellDeck (filterable grid)
 * Right side: Preview card of selected spell
 * Bottom: Confirm button adds selected spells
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import SpellDeck from "../cards/SpellDeck";
import SpellCard from "../cards/SpellCard";
import type { Spell } from "../../hooks/useSpells";

interface SpellPickerModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (spells: Spell[]) => void;
  /** Names of spells already on the character (to disable re-adding) */
  existingNames?: Set<string>;
}

export default function SpellPickerModal({
  open,
  onClose,
  onConfirm,
  existingNames = new Set(),
}: SpellPickerModalProps) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<Spell[]>([]);
  const selectedNames = new Set([
    ...existingNames,
    ...selected.map((s) => s.name),
  ]);

  // Preview the last selected spell
  const preview = selected.length > 0 ? selected[selected.length - 1] : null;

  function handleSelect(spell: Spell) {
    if (existingNames.has(spell.name)) return;

    setSelected((prev) => {
      const exists = prev.find((s) => s.name === spell.name);
      if (exists) return prev.filter((s) => s.name !== spell.name);
      return [...prev, spell];
    });
  }

  function handleConfirm() {
    onConfirm(selected);
    setSelected([]);
    onClose();
  }

  function handleClose() {
    setSelected([]);
    onClose();
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            className="relative bg-bg border border-border rounded-xl shadow-2xl
                       w-[90vw] max-w-5xl h-[80vh] flex flex-col overflow-hidden"
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Sparkles size={20} className="text-accent" />
                <h2 className="font-display text-accent text-lg">
                  {t("spells.pickSpells")}
                </h2>
                {selected.length > 0 && (
                  <span className="bg-accent/20 text-accent text-sm px-2 py-0.5 rounded-full">
                    {selected.length} {t("spells.selected")}
                  </span>
                )}
              </div>
              <button
                onClick={handleClose}
                className="text-text-muted hover:text-text-primary transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Body: grid + preview */}
            <div className="flex flex-1 overflow-hidden">
              {/* Left: Spell browser */}
              <div className="flex-1 overflow-y-auto p-4">
                <SpellDeck
                  onSelect={handleSelect}
                  selectedNames={selectedNames}
                />
              </div>

              {/* Right: Preview panel */}
              <div className="w-72 border-l border-border p-4 flex flex-col">
                <h3 className="text-text-muted text-sm uppercase tracking-wider mb-3">
                  {t("spells.preview")}
                </h3>

                {preview ? (
                  <div className="flex-1">
                    <SpellCard spell={preview} compact />
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <p className="text-text-muted text-sm text-center">
                      {t("spells.selectToPreview")}
                    </p>
                  </div>
                )}

                {/* Selected list */}
                {selected.length > 0 && (
                  <div className="mt-4 space-y-1 max-h-32 overflow-y-auto">
                    <p className="text-text-muted text-sm mb-1">{t("spells.selected")}:</p>
                    {selected.map((s) => (
                      <div
                        key={s.name}
                        className="flex items-center justify-between text-sm text-text-primary bg-surface rounded px-2 py-1.5"
                      >
                        <span className="truncate">{s.name}</span>
                        <button
                          onClick={() => handleSelect(s)}
                          className="text-text-muted hover:text-danger ml-2"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-sm text-text-muted hover:text-text transition-colors"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={handleConfirm}
                disabled={selected.length === 0}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg font-semibold
                           transition-colors disabled:opacity-40 disabled:cursor-not-allowed
                           bg-accent text-bg hover:bg-accent/90"
              >
                <Plus size={14} />
                {t("spells.addSelected", { count: selected.length })}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
