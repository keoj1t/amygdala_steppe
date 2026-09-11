"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/app/header";
import { Sidebar } from "@/components/app/sidebar";
import { Toaster } from "@/components/ui/toaster";
import { useAuthStore } from "@/store/auth-store";
import { useThemeStore } from "@/store/theme-store";

export function ProtectedShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, bootstrapped, loadSession } = useAuthStore();
  const { theme, hydrate } = useThemeStore();

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (bootstrapped && !user) {
      router.replace("/login");
    }
  }, [bootstrapped, router, user]);

  if (!bootstrapped || !user) {
    return <div className="grid min-h-screen place-items-center bg-black text-sm font-semibold text-white">amygdala content factory</div>;
  }

  return (
    <div className={theme === "light" ? "theme-light min-h-screen bg-[#ADD8E6] text-black" : "min-h-screen bg-black text-white"}>
      <Header />
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="w-full min-w-0 p-3 md:p-6">{children}</main>
      </div>
      <Toaster />
    </div>
  );
}
