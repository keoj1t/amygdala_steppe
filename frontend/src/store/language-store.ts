"use client";

import { create } from "zustand";
import { i18next } from "@/i18n/client";
import type { Language } from "@/i18n/resources";

type LanguageState = {
  language: Language;
  setLanguage: (language: Language) => void;
  loadLanguage: () => void;
};

const languages = ["kk", "ru", "en"] as const;

function isLanguage(value: string | undefined): value is Language {
  return languages.some((language) => language === value);
}

export const useLanguageStore = create<LanguageState>((set) => ({
  language: "en",
  setLanguage: (language) => {
    document.cookie = `language=${language}; path=/; max-age=31536000; SameSite=Lax`;
    void i18next.changeLanguage(language);
    set({ language });
  },
  loadLanguage: () => {
    const cookieLanguage = document.cookie
      .split("; ")
      .find((row) => row.startsWith("language="))
      ?.split("=")[1];
    const language = isLanguage(cookieLanguage) ? cookieLanguage : "en";
    void i18next.changeLanguage(language);
    set({ language });
  }
}));
