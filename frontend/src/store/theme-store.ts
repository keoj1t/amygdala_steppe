"use client";

import { create } from "zustand";

type Theme = "dark" | "light";

type ThemeState = {
  theme: Theme;
  hydrated: boolean;
  hydrate: () => void;
  toggle: () => void;
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: "dark",
  hydrated: false,
  hydrate: () => {
    const savedTheme = window.localStorage.getItem("theme");
    set({ theme: savedTheme === "light" ? "light" : "dark", hydrated: true });
  },
  toggle: () => {
    const theme = get().theme === "dark" ? "light" : "dark";
    window.localStorage.setItem("theme", theme);
    set({ theme });
  }
}));
