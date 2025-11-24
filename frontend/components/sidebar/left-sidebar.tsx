"use client";

import React from "react";
import { DotsThree, CaretDown, CaretRight, Clock, Users, Sparkle } from "phosphor-react";
import { PageList } from "./page-list";
import { CommunityCreations } from "./community-creations";
import { Button } from "../ui/button";

export function LeftSidebar() {
  const [isCommunityOpen, setIsCommunityOpen] = React.useState(true);

  return (
    <aside className="flex h-full w-full flex-col bg-transparent">
      <div className="flex-1 overflow-y-auto py-4 scrollbar-hide">
        {/* 我的页面 */}
        <div className="px-3 mb-6">
          <div className="flex items-center justify-between mb-3 px-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              我的页面
            </h3>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-gray-400 hover:text-[#6366F1] hover:bg-[#6366F1]/5"
            >
              <DotsThree size={18} weight="bold" />
            </Button>
          </div>

          <div className="space-y-1.5">
            <Button
              className="w-full justify-start gap-2.5 bg-gradient-to-r from-[#6366F1]/10 to-[#8B5CF6]/10 hover:from-[#6366F1]/15 hover:to-[#8B5CF6]/15 text-[#6366F1] border border-[#6366F1]/20 shadow-sm h-10 rounded-lg font-medium transition-all"
              variant="ghost"
              onClick={() => (window.location.href = "/workspace/new")}
            >
              <Sparkle size={16} className="text-[#6366F1]" weight="fill" />
              开始新对话
            </Button>
          </div>
        </div>

        {/* 最近更新 */}
        <div className="px-3 mb-6">
          <div className="flex items-center gap-2 mb-3 px-2">
            <Clock size={12} className="text-gray-400" weight="bold" />
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              最近更新
            </h3>
          </div>
          <div className="space-y-1.5">
            <PageList />
          </div>
        </div>

        {/* 社区创作 */}
        <div className="px-3">
          <button
            onClick={() => setIsCommunityOpen(!isCommunityOpen)}
            className="flex w-full items-center justify-between px-2 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider hover:text-[#6366F1] transition-colors rounded-lg hover:bg-[#6366F1]/5"
          >
            <div className="flex items-center gap-2">
              <Users size={12} weight="bold" />
              <span>社区创作</span>
            </div>
            {isCommunityOpen ? (
              <CaretDown size={12} weight="bold" />
            ) : (
              <CaretRight size={12} weight="bold" />
            )}
          </button>

          <div
            className={`grid transition-all duration-300 ease-in-out ${isCommunityOpen
                ? "grid-rows-[1fr] opacity-100 mt-2"
                : "grid-rows-[0fr] opacity-0"
              }`}
          >
            <div className="overflow-hidden">
              <CommunityCreations />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
