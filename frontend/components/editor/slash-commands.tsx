"use client";

import React from "react";
import type { Editor } from "@tiptap/react";
import { Card } from "../ui/card";
import {
    Sparkle,
    Code,
    ListBullets,
    ListNumbers,
    TextHOne,
    TextHTwo,
    Quotes,
} from "phosphor-react";

interface SlashCommand {
    title: string;
    description: string;
    icon: React.ElementType;
    command: () => void;
}

interface SlashCommandsProps {
    editor: Editor;
    onClose: () => void;
    position: { top: number; left: number };
}

export function SlashCommands({ editor, onClose, position }: SlashCommandsProps) {
    const [search, setSearch] = React.useState("");
    const [selectedIndex, setSelectedIndex] = React.useState(0);

    const commands: SlashCommand[] = [
        {
            title: "标题 1",
            description: "大标题",
            icon: TextHOne,
            command: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
        },
        {
            title: "标题 2",
            description: "中标题",
            icon: TextHTwo,
            command: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
        },
        {
            title: "无序列表",
            description: "创建项目符号列表",
            icon: ListBullets,
            command: () => editor.chain().focus().toggleBulletList().run(),
        },
        {
            title: "有序列表",
            description: "创建编号列表",
            icon: ListNumbers,
            command: () => editor.chain().focus().toggleOrderedList().run(),
        },
        {
            title: "代码块",
            description: "插入代码片段",
            icon: Code,
            command: () => editor.chain().focus().toggleCodeBlock().run(),
        },
        {
            title: "引用",
            description: "插入引用块",
            icon: Quotes,
            command: () => editor.chain().focus().toggleBlockquote().run(),
        },
        {
            title: "AI 助手",
            description: "调用 AI 帮助写作",
            icon: Sparkle,
            command: () => {
                // Placeholder for AI assistant
                console.log("AI助手功能");
            },
        },
    ];

    const filteredCommands = commands.filter(
        (cmd) =>
            cmd.title.toLowerCase().includes(search.toLowerCase()) ||
            cmd.description.toLowerCase().includes(search.toLowerCase())
    );

    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelectedIndex((i) => (i + 1) % filteredCommands.length);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelectedIndex((i) => (i - 1 + filteredCommands.length) % filteredCommands.length);
            } else if (e.key === "Enter") {
                e.preventDefault();
                filteredCommands[selectedIndex]?.command();
                onClose();
            } else if (e.key === "Escape") {
                e.preventDefault();
                onClose();
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [selectedIndex, filteredCommands, onClose]);

    return (
        <Card
            className="w-80 max-h-96 overflow-auto shadow-xl border border-gray-200"
            style={{
                position: "fixed",
                top: position.top,
                left: position.left,
                zIndex: 50,
            }}
        >
            <div className="p-2">
                <input
                    type="text"
                    placeholder="搜索命令..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                    autoFocus
                />
            </div>

            <div className="py-1">
                {filteredCommands.map((cmd, index) => {
                    const Icon = cmd.icon;
                    return (
                        <button
                            key={cmd.title}
                            onClick={() => {
                                cmd.command();
                                onClose();
                            }}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-colors ${index === selectedIndex
                                    ? "bg-primary/10 text-primary"
                                    : "hover:bg-gray-100 text-gray-700"
                                }`}
                        >
                            <div
                                className={`flex h-8 w-8 items-center justify-center rounded-lg ${index === selectedIndex ? "bg-primary/20" : "bg-gray-100"
                                    }`}
                            >
                                <Icon size={18} weight="bold" />
                            </div>
                            <div className="flex-1">
                                <div className="text-sm font-medium">{cmd.title}</div>
                                <div className="text-xs text-gray-500">{cmd.description}</div>
                            </div>
                        </button>
                    );
                })}
            </div>

            {filteredCommands.length === 0 && (
                <div className="px-3 py-8 text-center text-sm text-gray-500">未找到匹配的命令</div>
            )}
        </Card>
    );
}
