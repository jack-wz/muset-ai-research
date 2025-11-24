"use client";

import React from "react";
import { useParams } from "next/navigation";
import { LeftSidebar } from "@/components/sidebar/left-sidebar";
import { RichTextEditor } from "@/components/editor/rich-text-editor";
import type { JSONContent } from "@tiptap/react";
import { ChatPanel } from "@/components/chat/chat-panel";
import { useAuthStore } from "@/lib/stores/auth";
import { apiClient } from "@/lib/api/client";
import { useWorkspaceStore, Project } from "@/lib/stores/workspace";
import { Button } from "@/components/ui/button";
import { ChatCircleDots } from "phosphor-react";

export default function WorkspaceIdPage() {
    const params = useParams();
    const workspaceId = params.workspaceId as string;
    const { currentProject, setProjects, setCurrentProject } = useWorkspaceStore();
    const { isAuthenticated } = useAuthStore();
    const [showChat, setShowChat] = React.useState(true);
    const [isLoading, setIsLoading] = React.useState(true);

    const loadWorkspaceData = React.useCallback(async () => {
        try {
            setIsLoading(true);
            const projects = await apiClient.getProjects(workspaceId) as Project[];
            setProjects(projects);

            // Set the first project as current, or create a new one
            if (projects.length > 0) {
                setCurrentProject(projects[0]);
            } else {
                // Create a default project
                const newProject = await apiClient.createProject(workspaceId, {
                    title: "无标题",
                }) as Project;
                setProjects([newProject]);
                setCurrentProject(newProject);
            }
        } catch (error) {
            console.error("Failed to load workspace data:", error);
        } finally {
            setIsLoading(false);
        }
    }, [workspaceId, setProjects, setCurrentProject]);

    React.useEffect(() => {
        if (!isAuthenticated) {
            window.location.href = "/login";
            return;
        }

        loadWorkspaceData();
    }, [workspaceId, isAuthenticated, loadWorkspaceData]);

    if (isLoading) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-background text-foreground">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                    <p className="text-lg font-medium text-muted-foreground">加载工作区中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
            {/* Left Sidebar - Glassmorphism */}
            <div className="glass-panel z-10 h-full w-80 border-r border-white/20">
                <LeftSidebar />
            </div>

            {/* Main Content Area */}
            <main className="relative flex flex-1 flex-col overflow-hidden">
                {/* Top Bar (Optional, for breadcrumbs or actions) */}
                <header className="glass-panel flex h-14 items-center justify-between border-b border-white/20 px-4">
                    <div className="text-sm font-medium text-muted-foreground">
                        {currentProject ? currentProject.title : "选择一个页面"}
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setShowChat(!showChat)}
                            className={showChat ? "bg-primary/10 text-primary" : ""}
                        >
                            <ChatCircleDots size={20} />
                        </Button>
                    </div>
                </header>

                {/* Editor Area */}
                <div className="flex-1 overflow-hidden bg-white/50 backdrop-blur-sm">
                    {currentProject ? (
                        <RichTextEditor
                            workspaceId={workspaceId}
                            projectId={currentProject.id}
                            initialContent={currentProject.content as JSONContent}
                        />
                    ) : (
                        <div className="flex h-full items-center justify-center text-muted-foreground">
                            选择或创建一个页面开始写作
                        </div>
                    )}
                </div>
            </main>

            {/* Right Chat Panel - Glassmorphism Overlay or Side */}
            {showChat && (
                <div className="glass-panel z-10 h-full w-96 border-l border-white/20 shadow-xl transition-all duration-300">
                    <ChatPanel workspaceId={workspaceId} onClose={() => setShowChat(false)} />
                </div>
            )}
        </div>
    );
}
