"use client";

import { useEffect } from "react";
import { useLanguageStore } from "@/store/language-store";
import type { Language } from "@/i18n/resources";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/store/theme-store";

const languages: Language[] = ["kk", "ru", "en"];

export function LanguageSwitcher() {
  const { language, setLanguage, loadLanguage } = useLanguageStore();
  const { theme } = useThemeStore();

  useEffect(() => {
    loadLanguage();
  }, [loadLanguage]);

  return (
    <div className={theme === "light" ? "flex rounded-xl border border-black/15 bg-white/60 p-1" : "flex rounded-xl border border-white/15 bg-black p-1"}>
      {languages.map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => setLanguage(item)}
          className={cn(
            "focus-ring h-8 rounded-lg px-3 text-xs font-semibold uppercase transition",
            language === item ? "bg-white text-black" : theme === "light" ? "text-black/55 hover:bg-black/10 hover:text-black" : "text-white/55 hover:bg-white/10 hover:text-white"
          )}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
