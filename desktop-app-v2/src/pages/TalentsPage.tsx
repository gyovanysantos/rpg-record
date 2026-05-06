import { useTranslation } from "react-i18next";
import { Star } from "lucide-react";

export default function TalentsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Star className="text-accent" size={28} />
          <h1 className="text-2xl font-display text-accent">
            {t("talents.title")}
          </h1>
        </div>
        <button className="btn-primary">{t("talents.addTalent")}</button>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("talents.noTalents")}</p>
      </div>
    </div>
  );
}
