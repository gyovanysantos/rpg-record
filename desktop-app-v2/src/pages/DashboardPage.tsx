import { useTranslation } from "react-i18next";
import { LayoutDashboard } from "lucide-react";

export default function DashboardPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <LayoutDashboard className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">
          {t("dashboard.title")}
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <h3 className="text-sm text-text-muted mb-1">
            {t("dashboard.totalSessions")}
          </h3>
          <p className="text-3xl font-bold text-accent">--</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-text-muted mb-1">
            {t("dashboard.totalCharacters")}
          </h3>
          <p className="text-3xl font-bold text-accent">--</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-text-muted mb-1">
            {t("dashboard.activeCampaign")}
          </h3>
          <p className="text-xl text-text-primary">--</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-display text-text-primary mb-4">
          {t("dashboard.recentSessions")}
        </h2>
        <p className="text-text-muted">{t("dashboard.noSessions")}</p>
      </div>
    </div>
  );
}
