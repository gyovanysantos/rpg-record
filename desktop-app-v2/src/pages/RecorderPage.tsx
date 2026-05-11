import { useTranslation } from "react-i18next";
import { Mic } from "lucide-react";

export default function RecorderPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Mic className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("recorder.title")}
        </h1>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("recorder.selectDevice")}</p>
      </div>
    </div>
  );
}
