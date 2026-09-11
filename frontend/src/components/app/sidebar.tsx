"use client";

import { BookOpen, ChevronLeft, LayoutDashboard, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import "@/i18n/client";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/store/sidebar-store";
import { useThemeStore } from "@/store/theme-store";

const navItems = [
  { href: "/dashboard", key: "nav.dashboard", label: "Дашборд", icon: LayoutDashboard },
  { href: "/dashboard/projects", key: "nav.projects", label: "Проекты", icon: Sparkles },
  { href: "/dashboard/brandbooks", key: "nav.brandbooks", label: "Брендбуки", icon: BookOpen }
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { open, close } = useSidebarStore();
  const { theme } = useThemeStore();

  return (
    <>
      <button type="button" aria-label="Закрыть меню" onClick={close} className={cn("fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition md:hidden", open ? "visible opacity-100" : "invisible opacity-0")} />
      <aside className={cn("group fixed inset-y-0 left-0 z-50 flex w-72 flex-col p-3 shadow-2xl backdrop-blur-xl transition-transform duration-300 md:sticky md:top-16 md:z-20 md:h-[calc(100vh-4rem)] md:w-16 md:translate-x-0 md:overflow-hidden md:hover:w-64 md:hover:shadow-[18px_0_60px_rgba(0,0,0,0.28)]", theme === "light" ? "border-r border-black/15 bg-[#ADD8E6]/95" : "border-r border-white/15 bg-black/95", open ? "translate-x-0" : "-translate-x-full md:translate-x-0") }>
        <div className="mb-6 flex items-center justify-between px-2 md:justify-center md:group-hover:justify-between">
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-white/35 md:hidden md:group-hover:block">Workspace</span>
          <button type="button" aria-label="Закрыть меню" onClick={close} className="grid h-9 w-9 place-items-center rounded-xl text-white/50 transition hover:bg-white/10 hover:text-white md:hidden">
            <X className="h-4 w-4" />
          </button>
          <ChevronLeft className="hidden h-4 w-4 text-white/25 md:block md:group-hover:hidden" />
        </div>
        <nav className="grid gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={close}
                title={item.label}
                className={cn("focus-ring flex h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition md:justify-center md:group-hover:justify-start", active ? "bg-[#CC5500] text-white shadow-[0_8px_24px_rgba(204,85,0,0.22)]" : theme === "light" ? "text-black/60 hover:bg-black/10 hover:text-black" : "text-white/55 hover:bg-white/8 hover:text-white")}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="md:hidden md:group-hover:inline">{t(item.key)}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
