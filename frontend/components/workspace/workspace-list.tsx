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

  const loadWorkspaces = React.useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getWorkspaces() as Workspace[];
      setWorkspaces(data);
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setIsLoading(false);
    }
  }, [setWorkspaces]);

  React.useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  const handleCreateWorkspace = async () => {
    try {
      const newWorkspace = await apiClient.createWorkspace({
        name: "无标题工作区",
      }) as Workspace;
      setWorkspaces([...workspaces, newWorkspace]);
      handleSelectWorkspace(newWorkspace);
    } catch (error) {
      console.error("Failed to create workspace:", error);
      alert("创建工作区失败");
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
    return <div className="text-center">加载工作区中...</div>;
  }

  return (
    <div className="container mx-auto max-w-6xl py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">工作区</h1>
          <p className="text-gray-600">选择一个工作区继续</p>
        </div>
        <Button onClick={handleCreateWorkspace}>
          <Plus size={20} weight="bold" />
          新建工作区
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
            placeholder="搜索工作区..."
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
          <p className="text-gray-500">未找到工作区</p>
          <Button className="mt-4" onClick={handleCreateWorkspace}>
            创建你的第一个工作区
          </Button>
        </div>
      )}
    </div>
  );
}
