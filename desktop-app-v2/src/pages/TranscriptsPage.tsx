import { useTranslation } from "react-i18next";
import { FileText } from "lucide-react";

export default function TranscriptsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <FileText className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("transcripts.title")}
        </h1>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("transcripts.noTranscripts")}</p>
      </div>
    </div>
  );
}
