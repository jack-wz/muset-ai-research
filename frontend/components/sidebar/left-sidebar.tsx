"use client";

import React from "react";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { PageList } from "./page-list";
import { CommunityCreations } from "./community-creations";

interface LeftSidebarProps {
  workspaceId: string;
}

export function LeftSidebar({ workspaceId }: LeftSidebarProps) {
  return (
    <aside className="w-80 border-r border-gray-200 bg-white">
      <div className="flex h-full flex-col">
        <PageList workspaceId={workspaceId} />
        <CommunityCreations />
      </div>
    </aside>
  );
}
