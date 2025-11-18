"use client";

import React from "react";
import { TopBar } from "./top-bar";
import { LeftSidebar } from "../sidebar/left-sidebar";
import { ChatPanel } from "../chat/chat-panel";

interface MainLayoutProps {
  children: React.ReactNode;
  workspaceId: string;
}

export function MainLayout({ children, workspaceId }: MainLayoutProps) {
  const [isChatOpen, setIsChatOpen] = React.useState(true);

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <LeftSidebar workspaceId={workspaceId} />
        <main className="flex-1 overflow-auto">{children}</main>
        {isChatOpen && (
          <ChatPanel
            workspaceId={workspaceId}
            onClose={() => setIsChatOpen(false)}
          />
        )}
      </div>
    </div>
  );
}
