"use client";

import { ArrowRight, FileText, Image, Link2, Palette, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import type { Route } from "next";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { GoldenSpiral } from "@/components/ui/golden-spiral";
import "@/i18n/client";
import { useGenerationStore } from "@/store/generation-store";
import { useThemeStore } from "@/store/theme-store";

export default function DashboardPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const { mode, input_text, setMode, setInputText } = useGenerationStore();
  const { theme } = useThemeStore();
  const [inputKind, setInputKind] = useState<"text" | "url">("text");
  const modes = [
    { id: "poster", label: t("dashboard.poster"), icon: Image },
    { id: "post", label: t("dashboard.post"), icon: FileText },
    { id: "background", label: t("dashboard.background"), icon: Palette }
  ] as const;

  function goToBrandbookSelection(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input_text.trim()) return;
    router.push("/dashboard/generation/select-brandbook" as Route);
  }

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-4rem)] w-full max-w-7xl flex-col justify-center py-3 md:py-6">
      <section className={theme === "light" ? "relative isolate flex min-h-[calc(100dvh-5rem)] flex-col justify-between overflow-hidden rounded-3xl border border-black/15 bg-[#ADD8E6] p-5 shadow-2xl md:p-8 lg:p-12" : "relative isolate flex min-h-[calc(100dvh-5rem)] flex-col justify-between overflow-hidden rounded-3xl border border-white/15 bg-black p-5 shadow-2xl md:p-8 lg:p-12"}>
        <div className="creative-grid pointer-events-none absolute -z-10 opacity-80" />
        <div className="golden-rule pointer-events-none -z-10" />
        <GoldenSpiral className="pointer-events-none absolute -right-12 top-8 -z-10 h-[78%] w-[78%]" stroke="#CC5500" opacity={theme === "light" ? 0.32 : 0.6} />
        <GoldenSpiral className="pointer-events-none absolute -bottom-24 -left-16 -z-10 h-[46%] w-[46%]" stroke="#ADD8E6" opacity={theme === "light" ? 0.28 : 0.5} />

        <header className="flex items-start justify-between gap-6">
          <div>
            <div className="mb-8 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.2em] text-[#CC5500]">
              <span className="grid h-9 w-9 place-items-center rounded-xl border border-[#CC5500]/30 bg-[#CC5500]/10"><Sparkles className="h-4 w-4" /></span>
              {t("dashboard.workspace")}
            </div>
            <p className={theme === "light" ? "mb-3 text-sm text-black/60" : "mb-3 text-sm text-white/45"}>{t("dashboard.eyebrow")}</p>
            <h1 className="max-w-3xl text-4xl font-semibold leading-[1.02] tracking-tight text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.25)] md:text-7xl">
              {t("dashboard.headline")}
            </h1>
          </div>
        </header>

        <div className="max-w-xl py-6 md:py-10">
          <p className="text-base leading-7 text-white/85 md:text-lg">{t("dashboard.helper")}</p>
        </div>

        <form onSubmit={goToBrandbookSelection} className={theme === "light" ? "rounded-2xl border border-black/15 bg-white/75 p-3 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur md:p-4" : "rounded-2xl border border-white/15 bg-black/80 p-3 shadow-[0_24px_80px_rgba(0,0,0,0.28)] backdrop-blur md:p-4"}>
          <div className="mb-3 flex items-center justify-between gap-3 px-2">
            <div className={theme === "light" ? "flex items-center gap-1 rounded-lg border border-black/15 bg-white p-1" : "flex items-center gap-1 rounded-lg border border-white/15 bg-black p-1"}>
              <button type="button" onClick={() => setInputKind("text")} className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${inputKind === "text" ? "bg-black text-white" : theme === "light" ? "text-black/55 hover:text-black" : "text-white/45 hover:text-white"}`}>{t("dashboard.inputText")}</button>
              <button type="button" onClick={() => setInputKind("url")} className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${inputKind === "url" ? "bg-black text-white" : theme === "light" ? "text-black/55 hover:text-black" : "text-white/45 hover:text-white"}`}>{t("dashboard.inputUrl")}</button>
            </div>
            <Link2 className={theme === "light" ? "mr-2 h-4 w-4 text-black/35" : "mr-2 h-4 w-4 text-white/45"} />
          </div>
          <textarea value={input_text} onChange={(event) => setInputText(event.target.value)} rows={3} required placeholder={inputKind === "url" ? t("dashboard.urlPlaceholder") : t("dashboard.textPlaceholder")} className={theme === "light" ? "focus-ring min-h-24 w-full resize-none border-0 bg-transparent px-2 py-2 text-base leading-7 text-black outline-none placeholder:text-black/35" : "focus-ring min-h-24 w-full resize-none border-0 bg-transparent px-2 py-2 text-base leading-7 text-white outline-none placeholder:text-white/25"} />
          <div className={theme === "light" ? "mt-3 flex flex-col gap-3 border-t border-black/15 pt-3 md:flex-row md:items-center md:justify-between" : "mt-3 flex flex-col gap-3 border-t border-white/15 pt-3 md:flex-row md:items-center md:justify-between"}>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {modes.map((item) => {
                const Icon = item.icon;
                const active = mode === item.id;
                return <button key={item.id} type="button" onClick={() => setMode(item.id)} aria-pressed={active} className={`flex min-w-36 items-center gap-2 rounded-xl border px-3 py-2 text-left transition ${active ? "border-[#CC5500] bg-[#CC5500]/15 text-black" : theme === "light" ? "border-transparent text-black/65 hover:border-black/15 hover:text-black" : "border-transparent text-white/80 hover:border-white/15 hover:text-white"}`}><Icon className="h-4 w-4 shrink-0" /><span className="block text-sm font-semibold">{item.label}</span></button>;
              })}
            </div>
            <Button type="submit" className="h-11 rounded-xl bg-[#CC5500] px-6 text-white hover:bg-[#CC5500]/80"><span>{t("dashboard.next")}</span><ArrowRight className="h-4 w-4" /></Button>
          </div>
        </form>
      </section>
    </div>
  );
}
