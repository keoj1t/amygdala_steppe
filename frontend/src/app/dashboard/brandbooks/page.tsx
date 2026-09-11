"use client";

import { ImagePlus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { ColorPicker } from "@/components/ui/color-picker";
import { Input } from "@/components/ui/input";
import "@/i18n/client";
import { api } from "@/lib/api";
import type { Brandbook, Project } from "@/lib/types";
import { useToastStore } from "@/store/toast-store";
import { useThemeStore } from "@/store/theme-store";

const hex = /^#[0-9A-Fa-f]{6}$/;

const schema = z.object({
  name: z.string().min(1).max(120),
  primary_color: z.string().regex(hex),
  secondary_color: z.string().regex(hex),
  text_color: z.string().regex(hex),
  background_color: z.string().regex(hex),
  font_header: z.string().min(1).max(120),
  font_body: z.string().min(1).max(120),
  font_family: z.string().min(1).max(120),
  logo: z.custom<FileList>().optional()
});

type FormValues = z.infer<typeof schema>;

const fontPairs = [
  ["Inter", "Inter"],
  ["Georgia", "Inter"],
  ["Arial", "Georgia"],
  ["Trebuchet MS", "Arial"],
  ["Playfair Display", "Manrope"],
  ["Space Grotesk", "Open Sans"],
  ["Montserrat", "Lora"],
  ["Merriweather", "Source Sans 3"],
  ["DM Serif Display", "DM Sans"],
  ["Cormorant Garamond", "Work Sans"],
  ["Bebas Neue", "Roboto"],
  ["Futura", "Helvetica Neue"],
  ["IBM Plex Sans", "IBM Plex Mono"],
  ["Roboto Slab", "Nunito Sans"]
] as const;

export default function BrandbooksPage() {
  const { t } = useTranslation();
  const { push } = useToastStore();
  const { theme } = useThemeStore();
  const [draftProjectId, setDraftProjectId] = useState<string | null>(null);
  const [brandbooks, setBrandbooks] = useState<Brandbook[]>([]);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      primary_color: "#CC5500",
      secondary_color: "#ADD8E6",
      text_color: "#000000",
      background_color: "#FFFFFF",
      font_header: "Inter",
      font_body: "Inter",
      font_family: "Inter"
    }
  });
  const values = form.watch();
  const logoFile = values.logo?.item(0);
  const logoPreview = useMemo(() => (logoFile ? URL.createObjectURL(logoFile) : null), [logoFile]);

  async function loadBrandbooks() {
    const { data } = await api.get<Brandbook[]>("/api/v1/brandbooks");
    setBrandbooks(data);
  }

  useEffect(() => {
    void loadBrandbooks();
  }, []);

  useEffect(() => {
    setDraftProjectId(new URLSearchParams(window.location.search).get("draft"));
  }, []);

  useEffect(() => {
    return () => {
      if (logoPreview) {
        URL.revokeObjectURL(logoPreview);
      }
    };
  }, [logoPreview]);

  async function onSubmit(values: FormValues) {
    try {
      const body = new FormData();
      body.append("name", values.name);
      body.append("primary_color", values.primary_color);
      body.append("secondary_color", values.secondary_color);
      body.append("text_color", values.text_color);
      body.append("background_color", values.background_color);
      body.append("font_header", values.font_header);
      body.append("font_body", values.font_body);
      body.append("font_family", values.font_family);
      const file = values.logo?.item(0);
      if (file) {
        body.append("logo", file);
      }
      const { data: brandbook } = await api.post<Brandbook>("/api/v1/brandbooks", body);
      if (draftProjectId) {
        await api.patch<Project>(`/api/v1/projects/${draftProjectId}`, { brandbook_id: brandbook.id });
      }
      form.reset({
        name: "",
        primary_color: "#CC5500",
        secondary_color: "#ADD8E6",
        text_color: "#000000",
        background_color: "#FFFFFF",
        font_header: "Inter",
        font_body: "Inter",
        font_family: "Inter"
      });
      await loadBrandbooks();
      push({ title: draftProjectId ? "Брендбук добавлен к черновику" : "Brandbook created", tone: "success" });
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Brandbook failed", tone: "error" });
    }
  }

  async function removeBrandbook(id: string) {
    try {
      await api.delete(`/api/v1/brandbooks/${id}`);
      setBrandbooks((items) => items.filter((item) => item.id !== id));
      push({ title: "Brandbook deleted", tone: "success" });
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Delete failed", tone: "error" });
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[460px_1fr]">
      <section className="rounded-xl border border-white/15 bg-black p-5 shadow-sm">
        <h1 className="mb-5 text-xl font-bold text-white">{t("brandbook.title")}</h1>
        <form className="grid gap-4" onSubmit={form.handleSubmit(onSubmit)}>
          <Input placeholder={t("brandbook.name")} {...form.register("name")} />
          <div className="grid gap-4 sm:grid-cols-2">
            <ColorPicker label={t("brandbook.primary")} value={values.primary_color} onChange={(value) => form.setValue("primary_color", value, { shouldValidate: true })} />
            <ColorPicker label={t("brandbook.secondary")} value={values.secondary_color} onChange={(value) => form.setValue("secondary_color", value, { shouldValidate: true })} />
            <ColorPicker label={t("brandbook.text")} value={values.text_color} onChange={(value) => form.setValue("text_color", value, { shouldValidate: true })} />
            <ColorPicker label={t("brandbook.background")} value={values.background_color} onChange={(value) => form.setValue("background_color", value, { shouldValidate: true })} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <select className="focus-ring h-10 rounded-xl border border-white/15 bg-black px-3 text-sm text-white shadow-sm sm:col-span-2" {...form.register("font_family")}>
              <option value="Inter">Inter (Minimalist / Tech)</option>
              <option value="Roboto">Roboto (Clean / Corporate)</option>
              <option value="Montserrat">Montserrat (Bold / Modern)</option>
              <option value="Playfair Display">Playfair Display (Serif / Luxury)</option>
              <option value="Oswald">Oswald (Poster / Dynamic)</option>
            </select>
            <select className="focus-ring h-10 rounded-xl border border-white/15 bg-black px-3 text-sm text-white shadow-sm" {...form.register("font_header")}>
              {fontPairs.map(([header]) => <option key={header} value={header}>{header}</option>)}
            </select>
            <select className="focus-ring h-10 rounded-xl border border-white/15 bg-black px-3 text-sm text-white shadow-sm" {...form.register("font_body")}>
              {[...new Set(fontPairs.map(([, body]) => body))].map((body) => <option key={body} value={body}>{body}</option>)}
            </select>
          </div>
          <label className="focus-ring flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-black px-4 py-5 text-sm font-semibold text-white transition hover:border-[#CC5500]">
            <ImagePlus className="h-4 w-4 text-brand-orange" />
            {t("brandbook.logo")}
            <input type="file" accept="image/*" className="sr-only" {...form.register("logo")} />
          </label>
          <Button type="submit" disabled={form.formState.isSubmitting}>{t("brandbook.create")}</Button>
        </form>
      </section>
      <section className="grid gap-6">
        <div className="rounded-xl border border-white/15 bg-black p-5 shadow-sm">
          <h2 className="mb-5 text-xl font-bold text-white">{t("brandbook.preview")}</h2>
          <div className="rounded-xl border border-black/10 p-5 transition" style={{ backgroundColor: theme === "dark" ? "#000000" : values.background_color, color: theme === "dark" ? "#FFFFFF" : values.text_color, fontFamily: values.font_body }}>
            <div className="mb-5 flex items-center gap-3">
              <div className="relative grid h-14 w-14 place-items-center overflow-hidden rounded-xl" style={{ backgroundColor: values.secondary_color }}>
                {logoPreview ? <img src={logoPreview} alt="" className="h-full w-full object-cover" /> : <span className="font-black" style={{ color: values.primary_color }}>AI</span>}
              </div>
              <div>
                <h3 className="text-2xl font-bold" style={{ fontFamily: values.font_header }}>{values.name || "Brand System"}</h3>
                <p className="text-sm opacity-70">amygdala content factory</p>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[values.primary_color, values.secondary_color, values.text_color].map((color) => (
                <div key={color} className={`rounded-xl border border-black/10 p-3 ${theme === "dark" ? "bg-black/70" : "bg-white/70"}`}>
                  <div className="mb-2 h-10 rounded-lg" style={{ backgroundColor: color }} />
                  <p className="text-xs font-semibold">{color}</p>
                </div>
              ))}
            </div>
            <Button type="button" className="mt-5" style={{ backgroundColor: values.primary_color }}>Generate brief</Button>
          </div>
        </div>
        <div className="rounded-xl border border-white/15 bg-black p-5 shadow-sm">
          <div className="grid gap-3">
            {brandbooks.map((brandbook) => (
              <article key={brandbook.id} className="grid gap-3 rounded-xl border border-white/15 p-4 md:grid-cols-[1fr_auto] md:items-center">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-xl border border-white/15 bg-white/10" style={{ backgroundColor: brandbook.secondary_color }}>
                    {brandbook.logo_url ? <img src={brandbook.logo_url} alt={`${brandbook.name} logo`} className="h-full w-full object-contain p-1" /> : <span className="font-bold" style={{ color: brandbook.primary_color }}>AI</span>}
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-white">{brandbook.name}</h3>
                    <p className="truncate text-sm text-white/45">{brandbook.font_header} / {brandbook.font_body}</p>
                  </div>
                </div>
                <Button type="button" variant="danger" size="icon" aria-label={t("brandbook.delete")} onClick={() => void removeBrandbook(brandbook.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
