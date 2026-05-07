/**
 * API hooks for spell data.
 * Uses @tanstack/react-query to fetch from FastAPI backend.
 */
import { useQuery } from "@tanstack/react-query";

export interface Spell {
  name: string;
  tradition: string;
  rank: number;
  description: string;
}

/** A spell on a character sheet — has casting tracking */
export interface CharacterSpell extends Spell {
  max_castings: number;
  current_castings: number;
}

const API = "/api/spells";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function useSpells(filters?: {
  tradition?: string;
  rank?: number;
  search?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.tradition) params.set("tradition", filters.tradition);
  if (filters?.rank !== undefined) params.set("rank", String(filters.rank));
  if (filters?.search) params.set("search", filters.search);

  const qs = params.toString();
  const url = qs ? `${API}?${qs}` : API;

  return useQuery<Spell[]>({
    queryKey: ["spells", filters],
    queryFn: () => fetchJson(url),
  });
}

export function useTraditions() {
  return useQuery<string[]>({
    queryKey: ["spells", "traditions"],
    queryFn: () => fetchJson(`${API}/traditions`),
  });
}
