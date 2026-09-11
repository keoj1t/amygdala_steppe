"use client";

import { create } from "zustand";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

type ProjectsState = {
  projects: Project[];
  fetchProjects: () => Promise<Project[]>;
  addProject: (project: Project) => void;
  setProjects: (projects: Project[]) => void;
  updateProject: (project: Project) => void;
  removeProject: (projectId: string) => void;
};

export const useProjectsStore = create<ProjectsState>((set) => ({
  projects: [],
  fetchProjects: async () => {
    const { data } = await api.get<Project[]>("/api/v1/projects");
    set({ projects: data });
    return data;
  },
  addProject: (project) => set((state) => ({ projects: [project, ...state.projects.filter((item) => item.id !== project.id)] })),
  setProjects: (projects) => set({ projects }),
  updateProject: (project) => set((state) => ({ projects: state.projects.map((item) => item.id === project.id ? project : item) })),
  removeProject: (projectId) => set((state) => ({ projects: state.projects.filter((item) => item.id !== projectId) }))
}));