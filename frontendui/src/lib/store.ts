import { create } from "zustand";

export const BRANCHES = ["Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee", "all"] as const;
export type Branch = (typeof BRANCHES)[number];

interface AppStore {
  branch: Branch;
  setBranch: (b: Branch) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  branch: "Conut",
  setBranch: (branch) => set({ branch }),
}));
