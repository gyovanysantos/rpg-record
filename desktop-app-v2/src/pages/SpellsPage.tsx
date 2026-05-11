/**
 * SpellsPage — Browse, filter, and read all spells from the SotDL database.
 *
 * This page shows the full spell deck from spells.json.
 * It's a READ-ONLY browser — adding spells to a character
 * happens from the Character Sheet page via SpellPickerModal.
 */
import { useTranslation } from "react-i18next";
import { Sparkles } from "lucide-react";
import SpellDeck from "../components/cards/SpellDeck";

export default function SpellsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Sparkles className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("spells.title")}
        </h1>
      </div>

      {/* Spell browser */}
      <SpellDeck />
    </div>
  );
}
