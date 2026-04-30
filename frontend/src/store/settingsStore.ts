import { create } from "zustand";
import { settingsApi } from "../api/settingsApi";
import type { CategoryOut, HouseholdOut } from "../types/settings";

interface SettingsState {
  household: HouseholdOut | null;
  categories: CategoryOut[];
  isLoading: boolean;
  fetchHousehold: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  setHousehold: (household: HouseholdOut) => void;
  setCategories: (categories: CategoryOut[]) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  household: null,
  categories: [],
  isLoading: false,

  setHousehold: (household) => set({ household }),

  setCategories: (categories) => set({ categories }),

  fetchHousehold: async () => {
    set({ isLoading: true });
    try {
      const { data } = await settingsApi.getHousehold();
      set({ household: data });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchCategories: async () => {
    const { data } = await settingsApi.listCategories();
    set({ categories: data });
  },
}));
