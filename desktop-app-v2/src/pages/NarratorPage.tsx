import { useTranslation } from "react-i18next";
import { BookOpen } from "lucide-react";

export default function NarratorPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <BookOpen className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("narrator.title")}
        </h1>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("narrator.selectVoice")}</p>
      </div>
    </div>
  );
}
