import { create } from "zustand";
import { persist } from "zustand/middleware";

type Role = "dm" | "player" | null;

interface AppState {
  role: Role;
  setRole: (role: Role) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      role: null,
      setRole: (role) => set({ role }),
      sidebarCollapsed: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: "rpg-record-app",
    }
  )
);
