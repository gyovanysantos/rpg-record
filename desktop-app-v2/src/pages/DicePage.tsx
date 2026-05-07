import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Dices } from "lucide-react";

interface RollResult {
  id: number;
  d20: number;
  boons: number;
  banes: number;
  bonusDice: number[];
  total: number;
}

let rollId = 0;

function rollD6(): number {
  return Math.floor(Math.random() * 6) + 1;
}

function rollD20(): number {
  return Math.floor(Math.random() * 20) + 1;
}

export default function DicePage() {
  const { t } = useTranslation();
  const [boons, setBoons] = useState(0);
  const [banes, setBanes] = useState(0);
  const [history, setHistory] = useState<RollResult[]>([]);

  const handleRoll = () => {
    const d20 = rollD20();
    const netDice = Math.abs(boons - banes);
    const bonusDice = Array.from({ length: netDice }, () => rollD6());
    const bonus = bonusDice.length > 0 ? Math.max(...bonusDice) : 0;
    const sign = boons >= banes ? 1 : -1;
    const total = d20 + sign * bonus;

    const result: RollResult = {
      id: ++rollId,
      d20,
      boons,
      banes,
      bonusDice,
      total: Math.max(total, 0),
    };

    setHistory((prev) => [result, ...prev.slice(0, 19)]);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Dices className="text-accent" size={28} />
        <h1 className="text-2xl font-display text-accent">{t("dice.title")}</h1>
      </div>

      <div className="card max-w-md">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm text-text-muted">{t("dice.boons")}</label>
            <div className="flex items-center gap-2">
              <button
                className="btn-ghost px-2 py-1"
                onClick={() => setBoons(Math.max(0, boons - 1))}
              >
                -
              </button>
              <span className="text-lg font-bold w-6 text-center text-success">
                {boons}
              </span>
              <button
                className="btn-ghost px-2 py-1"
                onClick={() => setBoons(boons + 1)}
              >
                +
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm text-text-muted">{t("dice.banes")}</label>
            <div className="flex items-center gap-2">
              <button
                className="btn-ghost px-2 py-1"
                onClick={() => setBanes(Math.max(0, banes - 1))}
              >
                -
              </button>
              <span className="text-lg font-bold w-6 text-center text-danger">
                {banes}
              </span>
              <button
                className="btn-ghost px-2 py-1"
                onClick={() => setBanes(banes + 1)}
              >
                +
              </button>
            </div>
          </div>

          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleRoll}
            className="btn-primary w-full text-lg py-3"
          >
            {t("dice.roll")}
          </motion.button>
        </div>
      </div>

      {/* Latest Result */}
      {history.length > 0 && (
        <motion.div
          key={history[0].id}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="card max-w-md text-center"
        >
          <p className="text-sm text-text-muted mb-2">{t("dice.result")}</p>
          <p className="text-6xl font-bold text-accent">{history[0].total}</p>
          <p className="text-sm text-text-muted mt-2">
            d20: {history[0].d20}
            {history[0].bonusDice.length > 0 &&
              ` | d6s: [${history[0].bonusDice.join(", ")}]`}
          </p>
        </motion.div>
      )}

      {/* History */}
      {history.length > 1 && (
        <div className="card max-w-md">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm text-text-muted">{t("dice.history")}</h2>
            <button
              className="btn-ghost text-sm"
              onClick={() => setHistory([])}
            >
              {t("dice.clearHistory")}
            </button>
          </div>
          <div className="space-y-1">
            {history.slice(1).map((r) => (
              <div
                key={r.id}
                className="flex justify-between text-sm text-text-muted"
              >
                <span>
                  d20: {r.d20} | +{r.boons}B -{r.banes}P
                </span>
                <span className="font-bold text-text-primary">{r.total}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
