/**
 * API hook to fetch creature templates for invocations.
 * Creature data comes from desktop-app/data/sotdl/creatures.json via the backend.
 */
import { useQuery } from "@tanstack/react-query";

export interface Creature {
  name: string;
  difficulty: number;
  creature_type: string;
  size: string;
  perception: number;
  defense: number;
  health: number;
  strength: number;
  agility: number;
  intellect: number;
  will: number;
  speed: number;
  traits: string;
  immunities: string;
  attack_options: string;
  special_attacks: string;
  description: string;
}

/** Also used as the Invocation type stored on characters. */
export type Invocation = Creature;

const API = "/api/game-data/creatures";

export function useCreatures() {
  return useQuery<Creature[]>({
    queryKey: ["creatures"],
    queryFn: async () => {
      const res = await fetch(API);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    },
  });
}
