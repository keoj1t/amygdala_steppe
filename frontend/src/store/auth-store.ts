"use client";

import { create } from "zustand";
import { api } from "@/lib/api";
import type { TokenPair, User } from "@/lib/types";

type AuthState = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  bootstrapped: boolean;
  setSession: (session: TokenPair) => void;
  loadSession: () => Promise<void>;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  bootstrapped: false,
  setSession: (session) => {
    localStorage.setItem("accessToken", session.access_token);
    localStorage.setItem("refreshToken", session.refresh_token);
    set({ user: session.user, accessToken: session.access_token, refreshToken: session.refresh_token, bootstrapped: true });
  },
  loadSession: async () => {
    const accessToken = localStorage.getItem("accessToken");
    const refreshToken = localStorage.getItem("refreshToken");
    if (!accessToken) {
      set({ bootstrapped: true });
      return;
    }
    try {
      const { data } = await api.get<User>("/api/v1/auth/me");
      set({ user: data, accessToken, refreshToken, bootstrapped: true });
    } catch {
      get().logout();
    }
  },
  logout: () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    set({ user: null, accessToken: null, refreshToken: null, bootstrapped: true });
  }
}));
