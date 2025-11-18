"use client";

import React from "react";
import { useParams } from "next/navigation";
import { MainLayout } from "@/components/layout/main-layout";
import { RichTextEditor } from "@/components/editor/rich-text-editor";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { useAuthStore } from "@/lib/stores/auth";
import { apiClient } from "@/lib/api/client";

export default function WorkspacePage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const { currentProject, setProjects, setCurrentProject } = useWorkspaceStore();
  const { isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    if (!isAuthenticated) {
      window.location.href = "/login";
      return;
    }

    loadWorkspaceData();
  }, [workspaceId, isAuthenticated]);

  const loadWorkspaceData = async () => {
    try {
      setIsLoading(true);
      const projects: any = await apiClient.getProjects(workspaceId);
      setProjects(projects);

      // Set the first project as current, or create a new one
      if (projects.length > 0) {
        setCurrentProject(projects[0]);
      } else {
        // Create a default project
        const newProject: any = await apiClient.createProject(workspaceId, {
          title: "Untitled",
        });
        setProjects([newProject]);
        setCurrentProject(newProject);
      }
    } catch (error) {
      console.error("Failed to load workspace data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4">
            <svg
              className="h-12 w-12 animate-spin text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <p className="text-gray-600">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!currentProject) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="mb-2 text-2xl font-bold">No project selected</h1>
          <p className="text-gray-600">Please create or select a project to continue.</p>
        </div>
      </div>
    );
  }

  return (
    <MainLayout workspaceId={workspaceId}>
      <RichTextEditor
        workspaceId={workspaceId}
        projectId={currentProject.id}
        initialContent={currentProject.content}
      />
    </MainLayout>
  );
}
