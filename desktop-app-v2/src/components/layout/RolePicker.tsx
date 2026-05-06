import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Crown, Sword } from "lucide-react";
import { useAppStore } from "../../stores/appStore";

export default function RolePicker() {
  const { t } = useTranslation();
  const setRole = useAppStore((s) => s.setRole);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center space-y-8"
      >
        <div>
          <h1 className="text-4xl font-display text-accent mb-2">
            {t("common.appName")}
          </h1>
          <p className="text-text-muted text-lg">{t("roles.subtitle")}</p>
        </div>

        <div className="flex gap-6">
          {/* Game Master Card */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setRole("dm")}
            className="card w-64 p-8 flex flex-col items-center gap-4
                       hover:border-accent transition-colors cursor-pointer group"
          >
            <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center
                            group-hover:bg-accent/30 transition-colors">
              <Crown className="w-8 h-8 text-accent" />
            </div>
            <h2 className="text-xl font-display text-text-primary">
              {t("roles.dm")}
            </h2>
            <p className="text-sm text-text-muted">{t("roles.dmDescription")}</p>
          </motion.button>

          {/* Player Card */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setRole("player")}
            className="card w-64 p-8 flex flex-col items-center gap-4
                       hover:border-accent transition-colors cursor-pointer group"
          >
            <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center
                            group-hover:bg-accent/30 transition-colors">
              <Sword className="w-8 h-8 text-accent" />
            </div>
            <h2 className="text-xl font-display text-text-primary">
              {t("roles.player")}
            </h2>
            <p className="text-sm text-text-muted">
              {t("roles.playerDescription")}
            </p>
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
