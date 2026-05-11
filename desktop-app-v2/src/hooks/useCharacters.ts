/**
 * API hooks for character CRUD.
 * Uses @tanstack/react-query + fetch to call FastAPI backend.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export interface CharacterSummary {
  name: string;
  filename: string;
}

export interface CharacterFull {
  name: string;
  filename: string;
  ancestry: string;
  level: number;
  novice_path: string;
  expert_path: string;
  master_path: string;
  strength: number;
  agility: number;
  intellect: number;
  will: number;
  health: number;
  health_current: number;
  health_bonus: number;
  healing_rate_bonus: number;
  defense: number;
  defense_bonus: number;
  perception: number;
  perception_bonus: number;
  healing_rate: number;
  speed_base: number;
  size: string;
  power: number;
  corruption: number;
  insanity: number;
  fortune: boolean;
  gold: number;
  damage_taken: number;
  is_injured: boolean;
  is_incapacitated: boolean;
  languages: string[];
  professions: string[];
  talents: Record<string, unknown>[];
  spells: Record<string, unknown>[];
  equipment: Record<string, unknown>[];
  invocations: Record<string, unknown>[];
  notes: string;
  portrait: string;
}

const API = "/api/characters";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/** List all characters (name + filename). */
export function useCharacters() {
  return useQuery<CharacterSummary[]>({
    queryKey: ["characters"],
    queryFn: () => fetchJson(API),
  });
}

/** Load full character data by filename. */
export function useCharacter(filename: string | null) {
  return useQuery<CharacterFull>({
    queryKey: ["characters", filename],
    queryFn: () => fetchJson(`${API}/${filename}`),
    enabled: !!filename,
  });
}

/** Create a new character. Returns { filename, name }. */
export function useCreateCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string }) => {
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`Create failed: ${res.status}`);
      return res.json() as Promise<{ filename: string; name: string }>;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["characters"] }),
  });
}

/** Delete a character by filename. */
export function useDeleteCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (filename: string) => {
      const res = await fetch(`${API}/${filename}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["characters"] }),
  });
}

/** Update a character. Sends full data, returns { filename, name }. */
export function useUpdateCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      filename,
      data,
    }: {
      filename: string;
      data: Partial<CharacterFull>;
    }) => {
      const res = await fetch(`${API}/${filename}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`Update failed: ${res.status}`);
      return res.json() as Promise<{ filename: string; name: string }>;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["characters", variables.filename] });
      qc.invalidateQueries({ queryKey: ["characters"] });
    },
  });
}
