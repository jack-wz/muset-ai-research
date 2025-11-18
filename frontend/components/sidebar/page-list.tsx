"use client";

import React from "react";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { Card } from "../ui/card";
import { ChatCircleDots } from "phosphor-react";
import { formatRelativeTime, truncate } from "@/lib/utils";

interface PageListProps {
  workspaceId: string;
}

export function PageList({ workspaceId }: PageListProps) {
  const { projects } = useWorkspaceStore();

  return (
    <div className="flex-shrink-0 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">My pages</h2>
        <button className="text-gray-500 hover:text-gray-700">•••</button>
      </div>

      <div className="mb-4">
        <button className="flex items-center gap-2 text-sm text-gray-600">
          <ChatCircleDots size={20} />
          Chat
        </button>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-500">Recently Updated</h3>
        {projects.slice(0, 3).map((project) => (
          <Card
            key={project.id}
            className="cursor-pointer p-4 transition-shadow hover:shadow-md"
          >
            <div className="mb-2 flex items-start justify-between">
              <h4 className="font-medium">{project.title}</h4>
              <button className="text-gray-400 hover:text-gray-600">•••</button>
            </div>
            <p className="mb-2 line-clamp-3 text-sm text-gray-600">
              {truncate(project.content?.text || "", 100)}
            </p>
            <p className="text-xs text-gray-400">
              {formatRelativeTime(project.updated_at)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
