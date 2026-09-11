"use client";

import { create } from "zustand";

type SidebarState = {
  open: boolean;
  toggle: () => void;
  close: () => void;
};

export const useSidebarStore = create<SidebarState>((set) => ({
  open: false,
  toggle: () => set((state) => ({ open: !state.open })),
  close: () => set({ open: false })
}));