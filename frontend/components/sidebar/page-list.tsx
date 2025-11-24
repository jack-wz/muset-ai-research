"use client";
// Force rebuild

import React from "react";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { Card } from "../ui/card";
import { ChatCircleDots } from "phosphor-react";
import { formatRelativeTime, truncate } from "@/lib/utils";

export function PageList() {
  const { projects } = useWorkspaceStore();

  return (
    <div className="flex-shrink-0 p-4">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-bold tracking-tight text-foreground/90">我的页面</h2>
        <button className="text-muted-foreground hover:text-foreground transition-colors">•••</button>
      </div>

      <div className="mb-6">
        <button className="glass-button flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-medium text-primary hover:text-primary/80">
          <ChatCircleDots size={20} />
          开始新对话
        </button>
      </div>

      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">最近更新</h3>
        {projects.slice(0, 3).map((project) => (
          <Card
            key={project.id}
            className="glass-panel cursor-pointer border-white/10 bg-white/5 p-4 transition-all hover:bg-white/10 hover:shadow-lg hover:ring-1 hover:ring-primary/30"
          >
            <div className="mb-2 flex items-start justify-between">
              <h4 className="font-semibold text-foreground">{project.title}</h4>
              <button className="text-muted-foreground hover:text-foreground">•••</button>
            </div>
            <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
              {truncate((project.content as any)?.text || "暂无内容...", 80)}
            </p>
            <p className="text-xs font-medium text-primary/60">
              {formatRelativeTime(project.updated_at)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
