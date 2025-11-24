"use client";

import React, { useState } from "react";
import { X, Gear } from "phosphor-react";
import { Button } from "../ui/button";
import { ModelConfigPanel } from "./model-config-panel";
import { MCPConfigPanel } from "./mcp-config-panel";
import { SkillsConfigPanel } from "./skills-config-panel";
import { VectorDBConfigPanel } from "./vector-db-config-panel";

type TabType = "general" | "models" | "mcp" | "skills" | "vectorDB";

interface SettingsDrawerProps {
    isOpen: boolean;
    onClose: () => void;
}

export function SettingsDrawer({ isOpen, onClose }: SettingsDrawerProps) {
    const [activeTab, setActiveTab] = useState<TabType>("models");
    const [isSaving, setIsSaving] = useState(false);

    // 关闭处理
    const handleClose = () => {
        onClose();
    };

    // ESC 键关闭
    React.useEffect(() => {
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isOpen) {
                handleClose();
            }
        };
        window.addEventListener("keydown", handleKey);
        return () => window.removeEventListener("keydown", handleKey);
    }, [isOpen]);

    // 保存配置
    const handleSave = async () => {
        setIsSaving(true);
        // TODO: 实际保存逻辑
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setIsSaving(false);
    };

    if (!isOpen) return null;

    const tabs = [
        { id: "general" as const, label: "通用" },
        { id: "models" as const, label: "模型" },
        { id: "mcp" as const, label: "MCP" },
        { id: "skills" as const, label: "技能包" },
        { id: "vectorDB" as const, label: "向量数据库" },
    ];

    return (
        <>
            {/* 遮罩层 */}
            <div
                className="fixed inset-0 bg-black/30 z-40 backdrop-blur-sm transition-opacity"
                onClick={handleClose}
            />

            {/* 抽屉 */}
            <div className="fixed right-0 top-0 bottom-0 w-full max-w-3xl bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col animate-slide-in-right">
                {/* 头部 */}
                <div className="flex items-center justify-between px-8 py-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Gear size={24} weight="fill" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">设置</h2>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleClose}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        <X size={24} weight="bold" />
                    </Button>
                </div>

                {/* 标签页 */}
                <div className="flex items-center gap-1 px-8 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                                    ? "bg-white dark:bg-gray-800 text-primary shadow-sm"
                                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/50"
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* 内容区域 */}
                <div className="flex-1 overflow-y-auto px-8 py-6">
                    {activeTab === "general" && (
                        <div className="space-y-6">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                    通用设置
                                </h3>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                    配置应用程序的基本设置和偏好。
                                </p>
                            </div>
                            {/* TODO: 通用设置表单 */}
                        </div>
                    )}
                    {activeTab === "models" && <ModelConfigPanel />}
                    {activeTab === "mcp" && <MCPConfigPanel />}
                    {activeTab === "skills" && <SkillsConfigPanel />}
                    {activeTab === "vectorDB" && <VectorDBConfigPanel />}
                </div>

                {/* 底部操作区 */}
                <div className="flex items-center justify-end gap-3 px-8 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                    <Button variant="ghost" onClick={handleClose}>
                        取消
                    </Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? "保存中..." : "保存更改"}
                    </Button>
                </div>
            </div>
        </>
    );
}

// 设置按钮组件(用于顶部导航栏)
interface SettingsButtonProps {
    onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
    return (
        <Button
            variant="ghost"
            size="icon"
            onClick={onClick}
            className="text-gray-600 hover:text-primary"
            aria-label="打开设置"
        >
            <Gear size={20} weight="bold" />
        </Button>
    );
}
