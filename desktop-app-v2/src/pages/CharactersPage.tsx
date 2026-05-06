import { useTranslation } from "react-i18next";
import { Users } from "lucide-react";

export default function CharactersPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="text-accent" size={28} />
          <h1 className="text-2xl font-display text-accent">
            {t("characters.title")}
          </h1>
        </div>
        <button className="btn-primary">{t("characters.newCharacter")}</button>
      </div>

      <div className="card">
        <p className="text-text-muted">{t("characters.noCharacters")}</p>
      </div>
    </div>
  );
}
