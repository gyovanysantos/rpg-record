/**
 * Tradition-to-color mapping for spell cards.
 * Each SotDL tradition gets a unique hue for its card accent border/badge.
 */

const TRADITION_COLORS: Record<string, string> = {
  // Elemental
  Fogo: "#e25822",
  Água: "#1e90ff",
  Ar: "#87ceeb",
  Terra: "#8b6914",
  Tempestade: "#6a5acd",
  Metal: "#a8a8a8",

  // Arcane / Learned
  Arcana: "#9b59b6",
  Encantamento: "#e91e9e",
  Ilusão: "#da70d6",
  Conjuração: "#ff6347",
  Teleporte: "#00ced1",
  Adivinhação: "#f0e68c",
  Runa: "#cd853f",
  Tecnomancia: "#48d1cc",

  // Nature / Primal
  Natureza: "#228b22",
  Primitiva: "#6b8e23",
  Transformação: "#ff8c00",

  // Divine / Light
  Vida: "#ffd700",
  Celestial: "#fffacd",
  Teurgia: "#f5deb3",
  Proteção: "#4682b4",

  // Dark / Forbidden
  Necromancia: "#556b2f",
  Sombra: "#2f2f4f",
  Maldição: "#800080",
  Proibida: "#8b0000",
  Demonologia: "#dc143c",
  Caos: "#ff4500",
  Destruição: "#b22222",
  Alma: "#dda0dd",

  // Social / Support
  Canção: "#ff69b4",
  Fada: "#98fb98",
  Batalha: "#c0392b",
  Tempo: "#708090",
  Alteração: "#20b2aa",
};

/** Get the accent color for a tradition. Falls back to gold. */
export function getTraditionColor(tradition: string): string {
  return TRADITION_COLORS[tradition] ?? "#c4a35a";
}

/** Get a rank label like "Rank 0" or "R0" */
export function getRankLabel(rank: number, short = false): string {
  if (short) return `R${rank}`;
  return `Rank ${rank}`;
}

/** Get rank badge background color based on rank level */
export function getRankBadgeColor(rank: number): string {
  const colors = [
    "#4a5568", // R0 — gray
    "#2e5e3e", // R1 — green
    "#1e4a7a", // R2 — blue
    "#6b3fa0", // R3 — purple
    "#8b6914", // R4 — gold-brown
    "#8b0000", // R5 — crimson
    "#c4a35a", // R6+
    "#c4a35a",
    "#c4a35a",
    "#c4a35a",
    "#c4a35a",
  ];
  return colors[rank] ?? "#c4a35a";
}
