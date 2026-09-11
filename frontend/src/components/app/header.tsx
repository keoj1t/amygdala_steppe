"use client";

import { LogOut, Menu, Moon, Sun, UserCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/app/language-switcher";
import { Button } from "@/components/ui/button";
import "@/i18n/client";
import { useAuthStore } from "@/store/auth-store";
import { useSidebarStore } from "@/store/sidebar-store";
import { useThemeStore } from "@/store/theme-store";
import { GoldenSpiral } from "@/components/ui/golden-spiral";

export function Header() {
  const router = useRouter();
  const { t } = useTranslation();
  const { user, logout } = useAuthStore();
  const { toggle } = useSidebarStore();
  const { theme, toggle: toggleTheme } = useThemeStore();

  return (
    <header className={theme === "light" ? "sticky top-0 z-40 flex h-16 items-center justify-between border-b border-black/15 bg-[#ADD8E6]/90 px-4 backdrop-blur md:px-6" : "sticky top-0 z-40 flex h-16 items-center justify-between border-b border-white/15 bg-black/90 px-4 backdrop-blur md:px-6"}>
      <div className="flex items-center gap-3">
        <Button type="button" variant="ghost" size="icon" aria-label="Открыть меню" onClick={toggle} className={theme === "light" ? "text-black hover:bg-black/10 md:hidden" : "text-white hover:bg-white/10 md:hidden"}>
          <Menu className="h-5 w-5" />
        </Button>
        <GoldenSpiral className="h-9 w-9 shrink-0" stroke="#CC5500" opacity={0.62} />
        <div>
          <p className={theme === "light" ? "text-sm font-bold leading-4 text-black" : "text-sm font-bold leading-4 text-white"}>amygdala content factory</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        <Button type="button" variant="ghost" size="icon" aria-label="Переключить тему" onClick={toggleTheme} className={theme === "light" ? "text-black hover:bg-black/10" : "text-white hover:bg-white/10"}>
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        <div className={theme === "light" ? "hidden items-center gap-2 rounded-xl border border-black/15 bg-white/60 px-3 py-2 text-sm sm:flex" : "hidden items-center gap-2 rounded-xl border border-white/15 bg-black px-3 py-2 text-sm sm:flex"}>
          <UserCircle className="h-4 w-4 text-[#CC5500]" />
          <span className={theme === "light" ? "max-w-44 truncate text-black/75" : "max-w-44 truncate text-white/75"}>{user?.email}</span>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={t("nav.logout")}
          onClick={() => {
            logout();
            router.push("/login");
          }}
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
