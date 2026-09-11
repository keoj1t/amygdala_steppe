"use client";

import { create } from "zustand";

export type Toast = {
  id: string;
  title: string;
  tone: "success" | "error" | "info";
};

type ToastState = {
  toasts: Toast[];
  push: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
};

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = crypto.randomUUID();
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    window.setTimeout(() => set((state) => ({ toasts: state.toasts.filter((item) => item.id !== id) })), 3500);
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }))
}));
