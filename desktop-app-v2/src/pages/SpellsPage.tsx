import { useTranslation } from "react-i18next";
import { Sparkles } from "lucide-react";

export default function SpellsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="text-accent" size={28} />
          <h1 className="text-2xl font-display text-accent">
            {t("spells.title")}
          </h1>
        </div>
        <button className="btn-primary">{t("spells.addSpell")}</button>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("spells.noSpells")}</p>
      </div>
    </div>
  );
}
