import { create } from "zustand";

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  title: string;
  content?: any;
  status: string;
  created_at: string;
  updated_at: string;
}

interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  currentProject: Project | null;
  projects: Project[];

  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  currentWorkspace: null,
  currentProject: null,
  projects: [],

  setWorkspaces: (workspaces) => set({ workspaces }),

  setCurrentWorkspace: (workspace) =>
    set({ currentWorkspace: workspace, currentProject: null, projects: [] }),

  setProjects: (projects) => set({ projects }),

  setCurrentProject: (project) => set({ currentProject: project }),

  addProject: (project) =>
    set((state) => ({ projects: [...state.projects, project] })),

  updateProject: (id, updates) =>
    set((state) => ({
      projects: state.projects.map((p) => (p.id === id ? { ...p, ...updates } : p)),
      currentProject:
        state.currentProject?.id === id
          ? { ...state.currentProject, ...updates }
          : state.currentProject,
    })),
}));
