import { useTranslation } from "react-i18next";
import { Swords } from "lucide-react";

export default function InitiativePage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Swords className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("initiative.title")}
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-lg font-display text-success mb-4">
            {t("initiative.fastTurn")}
          </h2>
          <p className="text-text-muted text-sm">
            {t("initiative.addCombatant")}
          </p>
        </div>

        <div className="card">
          <h2 className="text-lg font-display text-danger mb-4">
            {t("initiative.slowTurn")}
          </h2>
          <p className="text-text-muted text-sm">
            {t("initiative.addCombatant")}
          </p>
        </div>
      </div>
    </div>
  );
}
