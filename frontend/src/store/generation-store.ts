"use client";

import { create } from "zustand";
import type { VisualStyle, ToneOfVoice, AspectRatio } from "@/lib/types";

export type GenerationMode = "poster" | "post" | "background";

type GenerationState = {
  mode: GenerationMode;
  aspect_ratio: AspectRatio;
  input_text: string;
  visual_style: VisualStyle;
  tone_of_voice: ToneOfVoice;
  selected_brandbook_id: string | null;
  image_url: string | null;
  draft_project_id: string | null;
  setMode: (mode: GenerationMode) => void;
  setAspectRatio: (aspect_ratio: AspectRatio) => void;
  setInputText: (input_text: string) => void;
  setVisualStyle: (visual_style: VisualStyle) => void;
  setToneOfVoice: (tone_of_voice: ToneOfVoice) => void;
  setSelectedBrandbookId: (selected_brandbook_id: string | null) => void;
  setImageUrl: (image_url: string | null) => void;
  setDraftProjectId: (draft_project_id: string | null) => void;
  reset: () => void;
};

export const useGenerationStore = create<GenerationState>((set) => ({
  mode: "poster",
  aspect_ratio: "1:1",
  input_text: "",
  visual_style: "Editorial Photo",
  tone_of_voice: "Expert",
  selected_brandbook_id: null,
  image_url: null,
  draft_project_id: null,
  setMode: (mode) =>
    set({
      mode,
      aspect_ratio: mode === "poster" ? "1:1" : mode === "post" ? "4:5" : "16:9",
    }),
  setAspectRatio: (aspect_ratio) => set({ aspect_ratio }),
  setInputText: (input_text) => set({ input_text }),
  setVisualStyle: (visual_style) => set({ visual_style }),
  setToneOfVoice: (tone_of_voice) => set({ tone_of_voice }),
  setSelectedBrandbookId: (selected_brandbook_id) => set({ selected_brandbook_id }),
  setImageUrl: (image_url) => set({ image_url }),
  setDraftProjectId: (draft_project_id) => set({ draft_project_id }),
  reset: () =>
    set({
      mode: "poster",
      aspect_ratio: "1:1",
      input_text: "",
      visual_style: "Editorial Photo",
      tone_of_voice: "Expert",
      selected_brandbook_id: null,
      image_url: null,
      draft_project_id: null,
    }),
}));