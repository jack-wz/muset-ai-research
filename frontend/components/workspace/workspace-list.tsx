"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { useWorkspaceStore, type Workspace } from "@/lib/stores/workspace";
import { apiClient } from "@/lib/api/client";
import { Plus, MagnifyingGlass } from "phosphor-react";
import { formatRelativeTime } from "@/lib/utils";

export function WorkspaceList() {
  const router = useRouter();
  const { workspaces, setWorkspaces, setCurrentWorkspace } = useWorkspaceStore();
  const [searchQuery, setSearchQuery] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setIsLoading(true);
      const data: any = await apiClient.getWorkspaces();
      setWorkspaces(data);
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
    try {
      console.log("Creating workspace...");
      const newWorkspace: any = await apiClient.createWorkspace({
        name: "Untitled Workspace",
      });
      console.log("Workspace created:", newWorkspace);
      setWorkspaces([...workspaces, newWorkspace]);
      handleSelectWorkspace(newWorkspace);
    } catch (error: any) {
      console.error("Failed to create workspace:", error);
      console.error("Error details:", {
        message: error.message,
        status: error.status,
        code: error.code,
      });
      alert(`Failed to create workspace: ${error.message || "Unknown error"}`);
    }
  };

  const handleSelectWorkspace = (workspace: Workspace) => {
    setCurrentWorkspace(workspace);
    router.push(`/workspace/${workspace.id}`);
  };

  const filteredWorkspaces = workspaces.filter((ws) =>
    ws.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return <div className="text-center">Loading workspaces...</div>;
  }

  return (
    <div className="container mx-auto max-w-6xl py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workspaces</h1>
          <p className="text-gray-600">Select a workspace to continue</p>
        </div>
        <Button onClick={handleCreateWorkspace}>
          <Plus size={20} weight="bold" />
          New Workspace
        </Button>
      </div>

      <div className="mb-6">
        <div className="relative">
          <MagnifyingGlass
            size={20}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <Input
            type="text"
            placeholder="Search workspaces..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredWorkspaces.map((workspace) => (
          <Card
            key={workspace.id}
            className="cursor-pointer transition-shadow hover:shadow-lg"
            onClick={() => handleSelectWorkspace(workspace)}
          >
            <CardHeader>
              <CardTitle>{workspace.name}</CardTitle>
              <CardDescription>{workspace.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">
                Updated {formatRelativeTime(workspace.updated_at)}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredWorkspaces.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-gray-500">No workspaces found</p>
          <Button className="mt-4" onClick={handleCreateWorkspace}>
            Create your first workspace
          </Button>
        </div>
      )}
    </div>
  );
}
