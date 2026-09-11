"use client";

import { Download, Edit3, Eye, Layers3, LoaderCircle, RefreshCw, Save, Sparkles, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import "@/i18n/client";
import { api } from "@/lib/api";
import type { Brandbook, Project } from "@/lib/types";
import { useToastStore } from "@/store/toast-store";
import { useProjectsStore } from "@/store/projects-store";

type SortMode = "brandbook" | "updated" | "title";
type ProjectTab = "brief" | "mockups";
type EditValues = { title: string; description: string; brandbook_id: string };

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const dynamicMockupScenes = [
  { id: "poster", label: "Постер в галерее", context: "poster_frame", fallback: `${apiBase}/static/mockups/poster.jpg` },
  { id: "instagram", label: "Instagram Смартфон", context: "phone", fallback: `${apiBase}/static/mockups/instagram.jpg` },
  { id: "linkedin", label: "Биллборд (Токио)", context: "billboard", fallback: `${apiBase}/static/mockups/linkedin.png` },
];

function resolveImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  return `${apiBase.replace(/\/$/, "")}/${url.replace(/^\//, "")}`;
}

export default function ProjectsPage() {
  const { t } = useTranslation();
  const { push } = useToastStore();
  const [brandbooks, setBrandbooks] = useState<Brandbook[]>([]);
  const [sortMode, setSortMode] = useState<SortMode>("updated");
  const [activeTabs, setActiveTabs] = useState<Record<string, ProjectTab>>({});
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<EditValues>({ title: "", description: "", brandbook_id: "" });
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});
  const [legacyImages, setLegacyImages] = useState<Record<string, string>>({});
  const [projectMockups, setProjectMockups] = useState<Record<string, Record<string, string>>>({});
  const [loadingMockups, setLoadingMockups] = useState<Record<string, boolean>>({});
  const [generatingDynamic, setGeneratingDynamic] = useState<Record<string, boolean>>({});
  const [isSaving, setIsSaving] = useState(false);
  const { projects, fetchProjects, updateProject, removeProject: removeProjectFromStore } = useProjectsStore();

  async function loadData() {
    const [, brandbookResponse] = await Promise.all([
      fetchProjects(),
      api.get<Brandbook[]>("/api/v1/brandbooks").catch(() => ({ data: [] })),
    ]);
    setBrandbooks(brandbookResponse.data);
  }

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    const storedImages: Record<string, string> = {};
    for (const project of projects) {
      if (!project.image_url && typeof window !== "undefined") {
        const cached = window.localStorage.getItem(`generation-output:${project.id}`);
        if (cached) {
          storedImages[project.id] = cached;
        }
      }
    }
    setLegacyImages(storedImages);
  }, [projects]);

  const sortedProjects = useMemo(() => {
    return [...projects].sort((first, second) => {
      if (sortMode === "title") return first.title.localeCompare(second.title);
      if (sortMode === "updated") return new Date(second.updated_at).getTime() - new Date(first.updated_at).getTime();
      return (first.brandbook?.name ?? "Без брендбука").localeCompare(second.brandbook?.name ?? "Без брендбука");
    });
  }, [projects, sortMode]);

  function startEditing(project: Project) {
    setEditingProjectId(project.id);
    setEditValues({
      title: project.title,
      description: project.description,
      brandbook_id: project.brandbook_id ?? "",
    });
  }

  async function saveProject(projectId: string) {
    setIsSaving(true);
    try {
      const { data } = await api.patch<Project>(`/api/v1/projects/${projectId}`, {
        ...editValues,
        brandbook_id: editValues.brandbook_id || null,
      });
      updateProject(data);
      setEditingProjectId(null);
      push({ title: "Проект обновлён", tone: "success" });
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Не удалось обновить проект", tone: "error" });
    } finally {
      setIsSaving(false);
    }
  }

  async function removeProject(id: string) {
    try {
      await api.delete(`/api/v1/projects/${id}`);
      removeProjectFromStore(id);
      push({ title: "Проект удалён", tone: "success" });
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Не удалось удалить проект", tone: "error" });
    }
  }

  async function generateMockupsForProject(projectId: string, imageUrl: string, sceneContext?: string) {
    if (sceneContext) {
      setGeneratingDynamic((prev) => ({ ...prev, [`${projectId}_${sceneContext}`]: true }));
    } else {
      setLoadingMockups((prev) => ({ ...prev, [projectId]: true }));
    }
    try {
      const { data } = await api.post<Record<string, string>>("/api/v1/generations/mockup", {
        project_id: projectId,
        image_url: imageUrl,
        scene_context: sceneContext || null,
      });
      setProjectMockups((prev) => ({
        ...prev,
        [projectId]: { ...(prev[projectId] || {}), ...data },
      }));
      push({ title: "Мокап успешно сформирован", tone: "success" });
    } catch (error) {
      push({
        title: error instanceof Error ? error.message : "Не удалось сформировать мокап",
        tone: "error",
      });
    } finally {
      if (sceneContext) {
        setGeneratingDynamic((prev) => ({ ...prev, [`${projectId}_${sceneContext}`]: false }));
      } else {
        setLoadingMockups((prev) => ({ ...prev, [projectId]: false }));
      }
    }
  }

  function handleTabChange(projectId: string, tab: ProjectTab, imageUrl: string | null) {
    setActiveTabs((tabs) => ({ ...tabs, [projectId]: tab }));
    if (tab === "mockups" && imageUrl && !projectMockups[projectId] && !loadingMockups[projectId]) {
      void generateMockupsForProject(projectId, imageUrl);
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-7xl gap-6">
      <header className="flex flex-col gap-4 border-b border-white/15 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-[#CC5500]">Workspace library</p>
          <h1 className="text-3xl font-semibold text-white md:text-5xl">{t("project.title")}</h1>
          <p className="mt-2 text-sm text-white/55">
            Все созданные постеры, посты и арт-дирекшн направления с автоматической генерацией мокапов.
          </p>
        </div>
        <label className="grid gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/45">
          Сортировка
          <select
            value={sortMode}
            onChange={(event) => setSortMode(event.target.value as SortMode)}
            className="focus-ring h-10 rounded-xl border border-white/15 bg-black px-3 text-sm font-medium normal-case tracking-normal text-white"
          >
            <option value="updated">По обновлению</option>
            <option value="brandbook">По брендбуку</option>
            <option value="title">По названию</option>
          </select>
        </label>
      </header>

      {sortedProjects.length === 0 ? (
        <section className="rounded-2xl border border-dashed border-[#CC5500]/50 bg-black p-10 text-center">
          <Layers3 className="mx-auto mb-4 h-8 w-8 text-[#CC5500]" />
          <h2 className="text-lg font-semibold text-white">Проектов пока нет</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-white/55">
            Начни с текста или ссылки на главном экране. Готовые постеры и посты сразу появятся здесь.
          </p>
        </section>
      ) : (
        <div className="grid gap-6">
          {sortedProjects.map((project) => {
            const activeTab = activeTabs[project.id] ?? "brief";
            const isEditing = editingProjectId === project.id;
            const brandbookName = project.brandbook?.name ?? "Без брендбука";
            const rawImageUrl = project.image_url || legacyImages[project.id] || null;
            const finalImageUrl = resolveImageUrl(rawImageUrl);
            const isPoster = project.title.toLowerCase().startsWith("постер") || project.title.toLowerCase().includes("poster");
            const dynamicMockups = projectMockups[project.id];
            const isMockupLoading = loadingMockups[project.id];

            return (
              <article key={project.id} className="rounded-2xl border border-white/15 bg-black p-4 shadow-sm md:p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                          isPoster
                            ? "bg-[#CC5500]/20 text-[#CC5500] border border-[#CC5500]/30"
                            : "bg-[#ADD8E6]/20 text-[#ADD8E6] border border-[#ADD8E6]/30"
                        }`}
                      >
                        {isPoster ? "Постер" : "Пост"}
                      </span>
                      <span className="inline-flex items-center gap-2 rounded-full border border-white/15 px-2.5 py-1 text-xs text-white/70">
                        {project.brandbook?.logo_url && (
                          <span
                            className="h-4 w-4 overflow-hidden rounded-full inline-block"
                            style={{ backgroundColor: project.brandbook.primary_color || "#CC5500" }}
                          >
                            <img src={resolveImageUrl(project.brandbook.logo_url) || ""} alt="" className="h-full w-full object-contain" />
                          </span>
                        )}
                        {brandbookName}
                      </span>
                    </div>

                    {isEditing ? (
                      <div className="grid gap-3">
                        <Input
                          value={editValues.title}
                          onChange={(event) => setEditValues((values) => ({ ...values, title: event.target.value }))}
                        />
                        <Textarea
                          value={editValues.description}
                          onChange={(event) => setEditValues((values) => ({ ...values, description: event.target.value }))}
                        />
                        <select
                          value={editValues.brandbook_id}
                          onChange={(event) => setEditValues((values) => ({ ...values, brandbook_id: event.target.value }))}
                          className="focus-ring h-10 rounded-xl border border-white/15 bg-black px-3 text-sm text-white"
                        >
                          <option value="">Без брендбука</option>
                          {brandbooks.map((brandbook) => (
                            <option key={brandbook.id} value={brandbook.id}>
                              {brandbook.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <>
                        <h2 className="text-xl font-semibold text-white">{project.title}</h2>
                        <p className="mt-2 max-w-3xl whitespace-pre-wrap text-sm leading-6 text-white/60">
                          {project.description}
                        </p>
                      </>
                    )}
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    {isEditing ? (
                      <>
                        <Button
                          type="button"
                          size="icon"
                          aria-label="Сохранить"
                          onClick={() => void saveProject(project.id)}
                          disabled={isSaving}
                        >
                          <Save className="h-4 w-4" />
                        </Button>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          aria-label="Отменить"
                          onClick={() => setEditingProjectId(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          aria-label="Редактировать"
                          onClick={() => startEditing(project)}
                        >
                          <Edit3 className="h-4 w-4" />
                        </Button>
                        <Button
                          type="button"
                          size="icon"
                          variant="danger"
                          aria-label="Удалить"
                          onClick={() => void removeProject(project.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleTabChange(project.id, "brief", finalImageUrl)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
                        activeTab === "brief" ? "bg-white text-black" : "text-white/60 hover:text-white"
                      }`}
                    >
                      Креатив
                    </button>
                    <button
                      type="button"
                      onClick={() => handleTabChange(project.id, "mockups", finalImageUrl)}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
                        activeTab === "mockups" ? "bg-white text-black" : "text-white/60 hover:text-white"
                      }`}
                    >
                      Мокапы
                      {isMockupLoading && <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[#CC5500]" />}
                    </button>
                  </div>

                  {finalImageUrl && activeTab === "mockups" && (
                    <button
                      type="button"
                      onClick={() => void generateMockupsForProject(project.id, finalImageUrl)}
                      disabled={isMockupLoading}
                      className="inline-flex items-center gap-1.5 text-xs text-white/50 hover:text-white"
                    >
                      <RefreshCw className={`h-3 w-3 ${isMockupLoading ? "animate-spin" : ""}`} />
                      Сгенерировать все мокапы
                    </button>
                  )}
                </div>

                {activeTab === "brief" && (
                  <div className="mt-4">
                    {finalImageUrl && !failedImages[project.id] ? (
                      <div className="relative overflow-hidden rounded-xl border border-white/15 bg-black/40">
                        <img
                          src={finalImageUrl}
                          alt={project.title}
                          className="max-h-[520px] w-full object-contain mx-auto"
                          onError={() => setFailedImages((items) => ({ ...items, [project.id]: true }))}
                        />
                        <div className="absolute bottom-3 right-3 flex gap-2">
                          <a
                            href={finalImageUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-lg bg-black/70 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur hover:bg-black"
                          >
                            <Eye className="h-3.5 w-3.5" /> Открыть
                          </a>
                          <a
                            href={finalImageUrl}
                            download={`creative_${project.id}.jpg`}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-[#CC5500] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#CC5500]/80"
                          >
                            <Download className="h-3.5 w-3.5" /> Скачать
                          </a>
                        </div>
                      </div>
                    ) : (
                      <div className="flex h-48 w-full items-center justify-center rounded-xl border border-dashed border-white/15 bg-white/[0.02] text-sm text-white/40">
                        {finalImageUrl && failedImages[project.id] ? "Ошибка загрузки изображения" : "Изображение ещё не сгенерировано"}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "mockups" && (
                  <div className="mt-4 grid gap-4 sm:grid-cols-3">
                    {dynamicMockupScenes.map((tpl) => {
                      const isDynamicLoading = generatingDynamic[`${project.id}_${tpl.context}`];
                      const compositedSrc =
                        dynamicMockups?.[tpl.id] ||
                        dynamicMockups?.[tpl.context] ||
                        dynamicMockups?.[tpl.id.toLowerCase()];
                      const imageSource = compositedSrc ? resolveImageUrl(compositedSrc) : tpl.fallback;

                      return (
                        <figure key={tpl.id} className="group relative overflow-hidden rounded-xl border border-white/15 bg-white/[0.03]">
                          <div className="relative aspect-[4/3] bg-black">
                            <img
                              src={imageSource || tpl.fallback}
                              alt={tpl.label}
                              loading="lazy"
                              className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"
                            />
                            {(isMockupLoading || isDynamicLoading) && !compositedSrc && (
                              <div className="absolute inset-0 grid place-items-center bg-black/50 backdrop-blur-xs">
                                <LoaderCircle className="h-6 w-6 animate-spin text-[#CC5500]" />
                              </div>
                            )}
                          </div>
                          <figcaption className="flex items-center justify-between px-3 py-2.5 text-xs font-semibold text-white/70">
                            <div>
                              <span>{tpl.label}</span>
                              {compositedSrc && (
                                <span className="ml-2 inline-block rounded bg-[#CC5500]/20 px-1.5 py-0.5 text-[10px] text-[#CC5500]">
                                  3D Mockup
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {finalImageUrl && (
                                <button
                                  type="button"
                                  title="Перегенерировать AI сцену"
                                  onClick={() => void generateMockupsForProject(project.id, finalImageUrl, tpl.context)}
                                  disabled={isDynamicLoading}
                                  className="text-white/40 hover:text-white"
                                >
                                  <Sparkles className={`h-3.5 w-3.5 ${isDynamicLoading ? "animate-spin text-[#CC5500]" : ""}`} />
                                </button>
                              )}
                              {imageSource && (
                                <a
                                  href={imageSource}
                                  download={`mockup_${tpl.id}_${project.id}.jpg`}
                                  title="Скачать мокап"
                                  className="text-white/50 hover:text-white"
                                >
                                  <Download className="h-3.5 w-3.5" />
                                </a>
                              )}
                            </div>
                          </figcaption>
                        </figure>
                      );
                    })}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
