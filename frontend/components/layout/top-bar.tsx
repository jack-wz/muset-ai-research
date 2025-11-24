"use client";

import React from "react";
import Image from "next/image";
import { useAuthStore } from "@/lib/stores/auth";
import { Button } from "../ui/button";
import { Plus, Sparkle, Lightning, User, Gear } from "phosphor-react";
import { SettingsDrawer } from "../settings/settings-drawer";

export function TopBar() {
  const { user } = useAuthStore();
  const [isSettingsOpen, setIsSettingsOpen] = React.useState(false);

  return (
    <>
      <header className="sticky top-0 z-50 h-16 border-b border-gray-100 bg-white/80 backdrop-blur-xl transition-all duration-200">
        <div className="mx-auto flex h-full max-w-screen-2xl items-center justify-between px-6">
          {/* 左侧区域 */}
          <div className="flex items-center gap-4">
            {/* Logo */}
            <div className="flex items-center gap-2.5 group cursor-pointer transition-opacity hover:opacity-80">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] shadow-sm shadow-primary/20">
                <Sparkle size={20} weight="fill" className="text-white" />
              </div>
              <span className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Muset.ai
              </span>
            </div>

            {/* 分隔线 */}
            <div className="h-5 w-px bg-gray-200" />

            {/* 新建页面按钮 */}
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-gray-600 hover:text-[#6366F1] hover:bg-[#6366F1]/5 font-medium transition-all"
              onClick={() => (window.location.href = "/workspace/new")}
            >
              <Plus size={16} weight="bold" />
              新建页面
            </Button>
          </div>

          {/* 右侧区域 */}
          <div className="flex items-center gap-3">
            {/* AI 积分显示 */}
            <div className="hidden items-center gap-2.5 rounded-full bg-gradient-to-r from-amber-50 to-orange-50 px-4 py-1.5 text-sm font-medium shadow-sm border border-amber-100/50 md:flex transition-all hover:shadow-md">
              <div className="flex items-center gap-1.5">
                <Lightning size={14} className="text-amber-500" weight="fill" />
                <span className="text-gray-900 font-semibold">35</span>
                <span className="text-gray-500 text-xs">积分</span>
              </div>
              <div className="h-3.5 w-px bg-amber-200" />
              <button className="text-xs font-bold text-[#6366F1] hover:text-[#4F46E5] transition-colors">
                升级
              </button>
            </div>

            {/* 设置按钮 */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSettingsOpen(true)}
              className="h-9 w-9 text-gray-500 hover:text-[#6366F1] hover:bg-[#6366F1]/5 transition-all"
              aria-label="打开设置"
            >
              <Gear size={20} weight="bold" />
            </Button>

            {/* 用户头像 */}
            <div className="flex items-center gap-2.5">
              <div className="hidden flex-col items-end sm:flex">
                <span className="text-sm font-semibold text-gray-900 leading-none">
                  {user?.name || "访客用户"}
                </span>
                <span className="text-xs text-gray-500 mt-0.5">免费计划</span>
              </div>

              <button className="group relative h-9 w-9 overflow-hidden rounded-full ring-2 ring-gray-100 transition-all hover:ring-[#6366F1]/30 hover:shadow-md">
                {user?.email ? (
                  <Image
                    src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.email}`}
                    alt="用户头像"
                    fill
                    className="object-cover transition-transform group-hover:scale-110"
                  />
                ) : (
                  <div className="h-full w-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500">
                    <User size={18} weight="bold" />
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Drawer */}
      <SettingsDrawer isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </>
  );
}
