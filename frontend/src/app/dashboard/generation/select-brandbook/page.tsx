"use client";

import { ArrowLeft, ArrowRight, Check, Crop, LoaderCircle, Palette, Plus, Sparkles, Type, Wand2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import {
  ASPECT_RATIOS,
  VISUAL_STYLES,
  TONES_OF_VOICE,
  type Brandbook,
  type Generation,
  type Project,
  type VisualStyle,
  type ToneOfVoice,
  type AspectRatio,
} from "@/lib/types";
import { useGenerationStore } from "@/store/generation-store";
import { useProjectsStore } from "@/store/projects-store";
import { useToastStore } from "@/store/toast-store";
import { useLanguageStore } from "@/store/language-store";

const ASPECT_RATIO_DESCRIPTIONS: Record<AspectRatio, string> = {
  "1:1": "Квадрат — Feed / Post",
  "9:16": "Вертикальный — Stories / Reels",
  "16:9": "Горизонтальный — Billboard / Banner",
  "4:5": "Портрет — Editorial Post",
};

export default function SelectBrandbookPage() {
  const router = useRouter();
  const { push } = useToastStore();
  const { addProject, fetchProjects } = useProjectsStore();
  const { language } = useLanguageStore();
  const {
    mode,
    aspect_ratio,
    input_text,
    visual_style,
    tone_of_voice,
    selected_brandbook_id,
    setSelectedBrandbookId,
    setDraftProjectId,
    setImageUrl,
    setAspectRatio,
    setVisualStyle,
    setToneOfVoice,
    reset,
  } = useGenerationStore();
  const [brandbooks, setBrandbooks] = useState<Brandbook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    void api
      .get<Brandbook[]>("/api/v1/brandbooks")
      .then(({ data }) => setBrandbooks(data))
      .catch((error) => {
        push({
          title: error instanceof Error ? error.message : "Не удалось загрузить брендбуки",
          tone: "error",
        });
      })
      .finally(() => setIsLoading(false));
  }, [push]);

  async function startGeneration(allowDraft = false) {
    if (!input_text.trim() || (!allowDraft && mode === "poster" && !selected_brandbook_id)) return;
    setIsSubmitting(true);
    try {
      const modeLabels: Record<string, string> = { poster: "Постер", post: "Пост", background: "Фон" };
      const typeLabel = modeLabels[mode] ?? mode;
      const { data: project } = await api.post<Project>("/api/v1/projects", {
        title: `${typeLabel} (${aspect_ratio}): ${input_text.trim().slice(0, 70)}`,
        description: input_text.trim(),
        brandbook_id: selected_brandbook_id,
      });
      if (allowDraft) {
        push({ title: "Черновик сохранён", tone: "success" });
        router.push("/dashboard/projects");
        return;
      }
      const sourceUrl = /^https?:\/\//i.test(input_text.trim()) ? input_text.trim() : null;
      setIsGenerating(true);
      const { data: generation } = await api.post<Generation>("/api/v1/generations", {
        project_id: project.id,
        prompt: input_text.trim(),
        mode,
        aspect_ratio,
        locale: language,
        brandbook_id: selected_brandbook_id,
        source_url: sourceUrl,
        visual_style,
        tone_of_voice,
      });
      if (generation.project) {
        addProject(generation.project);
      } else {
        await fetchProjects();
      }
      if (generation.image_url || generation.output) {
        const output =
          generation.image_url ?? (Array.isArray(generation.output) ? generation.output[0] : generation.output);
        if (output) {
          setImageUrl(output);
          window.localStorage.setItem(`generation-output:${project.id}`, output);
        }
      }
      if (generation.headline) {
        window.localStorage.setItem(`generation-headline:${project.id}`, generation.headline);
      }
      if (generation.post_text) {
        window.localStorage.setItem(`generation-post_text:${project.id}`, generation.post_text);
      }
      push({ title: "Генерация завершена!", tone: "success" });
      reset();
      router.push("/dashboard/projects");
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Не удалось запустить генерацию", tone: "error" });
    } finally {
      setIsSubmitting(false);
      setIsGenerating(false);
    }
  }

  async function saveDraftAndOpenBrandbook() {
    if (!input_text.trim()) return;
    setIsSubmitting(true);
    try {
      const { data } = await api.post<Project>("/api/v1/projects", {
        title: `Постер: ${input_text.trim().slice(0, 80)}`,
        description: input_text.trim(),
        brandbook_id: null,
      });
      setDraftProjectId(data.id);
      push({ title: "Черновик сохранён", tone: "success" });
      router.push(`/dashboard/brandbooks?draft=${data.id}`);
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Не удалось сохранить черновик", tone: "error" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-6rem)] w-full max-w-7xl py-3 md:py-8">
      <section className="min-h-[calc(100vh-7rem)] rounded-3xl border border-white/15 bg-black p-5 md:p-10">
        {isGenerating && (
          <div className="fixed inset-0 z-[70] grid place-items-center bg-black/75 p-6 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/15 bg-black p-6 text-white shadow-2xl">
              <div className="mb-5 flex items-center gap-3">
                <LoaderCircle className="h-6 w-6 animate-spin text-[#CC5500]" />
                <p className="font-semibold">AI Content Factory генерирует визуал</p>
              </div>
              <div className="space-y-2 text-xs text-white/55">
                <p>1. Grok формирует рекламный арт-дирекшн и промпт...</p>
                <p>2. FLUX создает изображение в формате {aspect_ratio}...</p>
                <p>3. PIL накладывает брендбук и формирует мокапы...</p>
              </div>
            </div>
          </div>
        )}

        <div className="mb-10 flex flex-col gap-6 border-b border-white/15 pb-8 md:flex-row md:items-end md:justify-between">
          <div>
            <Link
              href="/dashboard"
              className="mb-6 inline-flex items-center gap-2 text-sm text-white/45 transition hover:text-white"
            >
              <ArrowLeft className="h-4 w-4" /> Назад к идее
            </Link>
            <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-[#CC5500]">
              <Sparkles className="h-4 w-4" /> Шаг 2 из 2
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white md:text-5xl">Настрой параметры.</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/45">
              Выбери соотношение сторон, визуальный стиль, тон коммуникации и брендбук для генерации.
            </p>
          </div>
          <div className="rounded-xl border border-white/15 bg-black px-4 py-3 text-sm text-white/55">
            <span className="text-white/30">Режим & Формат</span>
            <br />
            <strong className="text-white">
              {mode === "poster" ? "Постер" : mode === "background" ? "Фон" : "Пост"} ({aspect_ratio})
            </strong>
          </div>
        </div>

        {/* Aspect Ratio Selector */}
        <div className="mb-8">
          <div className="mb-4 flex items-center gap-2">
            <Crop className="h-4 w-4 text-[#CC5500]" />
            <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-white/60">Соотношение сторон (Aspect Ratio)</h2>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {ASPECT_RATIOS.map((ratio) => {
              const active = aspect_ratio === ratio;
              return (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`flex flex-col items-start rounded-2xl border p-4 text-left transition ${
                    active
                      ? "border-[#CC5500] bg-[#CC5500]/15 text-white"
                      : "border-white/15 bg-white/[0.02] text-white/65 hover:border-white/30 hover:text-white"
                  }`}
                >
                  <span className="text-lg font-bold">{ratio}</span>
                  <span className="mt-1 text-xs text-white/45">{ASPECT_RATIO_DESCRIPTIONS[ratio]}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Visual Style Picker */}
        <div className="mb-8">
          <div className="mb-4 flex items-center gap-2">
            <Palette className="h-4 w-4 text-[#CC5500]" />
            <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-white/60">Визуальный стиль</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {VISUAL_STYLES.map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => setVisualStyle(style)}
                className={`rounded-xl border px-3.5 py-2 text-xs font-semibold transition ${
                  visual_style === style
                    ? "border-[#CC5500] bg-[#CC5500] text-white"
                    : "border-white/15 bg-white/[0.03] text-white/70 hover:border-white/30 hover:text-white"
                }`}
              >
                {style}
              </button>
            ))}
          </div>
        </div>

        {/* Tone of Voice Picker */}
        <div className="mb-10">
          <div className="mb-4 flex items-center gap-2">
            <Type className="h-4 w-4 text-[#CC5500]" />
            <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-white/60">Тон коммуникации</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {TONES_OF_VOICE.map((tone) => (
              <button
                key={tone}
                type="button"
                onClick={() => setToneOfVoice(tone)}
                className={`rounded-xl border px-3.5 py-2 text-xs font-semibold transition ${
                  tone_of_voice === tone
                    ? "border-[#ADD8E6] bg-[#ADD8E6]/20 text-[#ADD8E6]"
                    : "border-white/15 bg-white/[0.03] text-white/70 hover:border-white/30 hover:text-white"
                }`}
              >
                {tone}
              </button>
            ))}
          </div>
        </div>

        {/* Brandbook Selection Section */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-white/60">Брендбук</h2>
            <Link
              href="/dashboard/brandbooks"
              className="inline-flex items-center gap-1.5 text-xs text-[#CC5500] hover:underline"
            >
              <Plus className="h-3.5 w-3.5" /> Создать новый
            </Link>
          </div>

          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-white/40">
              <LoaderCircle className="h-5 w-5 animate-spin" />
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <button
                type="button"
                onClick={() => setSelectedBrandbookId(null)}
                className={`flex flex-col justify-between rounded-2xl border p-5 text-left transition ${
                  selected_brandbook_id === null
                    ? "border-[#CC5500] bg-[#CC5500]/10"
                    : "border-white/15 bg-white/[0.02] hover:border-white/30"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">Без брендбука</span>
                    {selected_brandbook_id === null && <Check className="h-4 w-4 text-[#CC5500]" />}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-white/45">
                    Использовать адаптивную коммерческую палитру (#CC5500 и #ADD8E6).
                  </p>
                </div>
              </button>

              {brandbooks.map((b) => {
                const isSelected = selected_brandbook_id === b.id;
                return (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => setSelectedBrandbookId(b.id)}
                    className={`flex flex-col justify-between rounded-2xl border p-5 text-left transition ${
                      isSelected
                        ? "border-[#CC5500] bg-[#CC5500]/10"
                        : "border-white/15 bg-white/[0.02] hover:border-white/30"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">{b.name}</span>
                        {isSelected && <Check className="h-4 w-4 text-[#CC5500]" />}
                      </div>
                      <div className="mt-3 flex items-center gap-2">
                        <span className="h-4 w-4 rounded-full border border-white/20" style={{ backgroundColor: b.primary_color }} />
                        <span className="h-4 w-4 rounded-full border border-white/20" style={{ backgroundColor: b.secondary_color }} />
                        <span className="h-4 w-4 rounded-full border border-white/20" style={{ backgroundColor: b.background_color }} />
                        <span className="text-xs text-white/50">{b.font_family || "Inter"}</span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Action Button Bar */}
        <div className="mt-10 flex flex-col gap-3 border-t border-white/15 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={() => void saveDraftAndOpenBrandbook()}
            disabled={isSubmitting}
            className="text-white/60 hover:text-white"
          >
            Сохранить черновик
          </Button>

          <Button
            type="button"
            onClick={() => void startGeneration(false)}
            disabled={isSubmitting || !input_text.trim()}
            className="h-12 rounded-xl bg-[#CC5500] px-8 text-base font-semibold text-white hover:bg-[#CC5500]/85"
          >
            <Wand2 className="h-5 w-5 mr-2" />
            <span>Сгенерировать контент</span>
          </Button>
        </div>
      </section>
    </div>
  );
}
