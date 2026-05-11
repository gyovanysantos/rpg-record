/**
 * API hooks for SotDL game reference data (ancestries, paths, traditions).
 */
import { useQuery } from "@tanstack/react-query";

export interface Ancestry {
  name: string;
  size: string;
  speed: number;
  attributes: Record<string, number>;
  languages: string[];
  traits: string[];
}

export interface NovicePath {
  name: string;
  attribute_bonuses: Record<string, number>;
  health_bonus: number;
  power_bonus?: number;
}

const API = "/api/game-data";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function useAncestries() {
  return useQuery<Ancestry[]>({
    queryKey: ["game-data", "ancestries"],
    queryFn: () => fetchJson(`${API}/ancestries`),
    staleTime: Infinity,
  });
}

export function useNovicePaths() {
  return useQuery<NovicePath[]>({
    queryKey: ["game-data", "paths", "novice"],
    queryFn: () => fetchJson(`${API}/paths/novice`),
    staleTime: Infinity,
  });
}

export function useExpertPaths() {
  return useQuery<string[]>({
    queryKey: ["game-data", "paths", "expert"],
    queryFn: () => fetchJson(`${API}/paths/expert`),
    staleTime: Infinity,
  });
}

export function useMasterPaths() {
  return useQuery<string[]>({
    queryKey: ["game-data", "paths", "master"],
    queryFn: () => fetchJson(`${API}/paths/master`),
    staleTime: Infinity,
  });
}
