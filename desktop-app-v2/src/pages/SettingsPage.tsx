import { useTranslation } from "react-i18next";
import { Settings } from "lucide-react";
import { useAppStore } from "../stores/appStore";

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const setRole = useAppStore((s) => s.setRole);

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem("language", lang);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Settings className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("settings.title")}
        </h1>
      </div>

      {/* Language */}
      <div className="card">
        <h2 className="text-lg font-display text-text-primary mb-4">
          {t("settings.language")}
        </h2>
        <p className="text-sm text-text-muted mb-3">
          {t("settings.languageDescription")}
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => handleLanguageChange("pt-BR")}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              i18n.language === "pt-BR"
                ? "border-accent bg-accent/15 text-accent"
                : "border-border text-text-muted hover:text-text-primary"
            }`}
          >
            {t("settings.portuguese")}
          </button>
          <button
            onClick={() => handleLanguageChange("en")}
            className={`px-4 py-2 rounded-lg border transition-colors ${
              i18n.language === "en"
                ? "border-accent bg-accent/15 text-accent"
                : "border-border text-text-muted hover:text-text-primary"
            }`}
          >
            {t("settings.english")}
          </button>
        </div>
      </div>

      {/* API Keys */}
      <div className="card">
        <h2 className="text-lg font-display text-text-primary mb-4">
          {t("settings.apiKeys")}
        </h2>
        <div className="space-y-3">
          <div>
            <label className="text-sm text-text-muted block mb-1">
              {t("settings.groqKey")}
            </label>
            <input type="password" className="input w-full" placeholder="gsk_..." />
          </div>
          <div>
            <label className="text-sm text-text-muted block mb-1">
              {t("settings.anthropicKey")}
            </label>
            <input type="password" className="input w-full" placeholder="sk-ant-..." />
          </div>
          <div>
            <label className="text-sm text-text-muted block mb-1">
              {t("settings.geminiKey")}
            </label>
            <input type="password" className="input w-full" placeholder="AI..." />
          </div>
          <button className="btn-primary">{t("settings.saveSettings")}</button>
        </div>
      </div>

      {/* Role */}
      <div className="card">
        <h2 className="text-lg font-display text-text-primary mb-4">
          {t("settings.role")}
        </h2>
        <button className="btn-ghost" onClick={() => setRole(null)}>
          {t("settings.changeRole")}
        </button>
      </div>
    </div>
  );
}
