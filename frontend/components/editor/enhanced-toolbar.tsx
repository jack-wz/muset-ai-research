"use client";

import React from "react";
import type { Editor } from "@tiptap/react";
import { Button } from "../ui/button";
import {
    TextBolder,
    TextItalic,
    TextStrikethrough,
    ListBullets,
    ListNumbers,
    Quotes,
    Code,
    TextHOne,
    TextHTwo,
    TextHThree,
} from "phosphor-react";

interface EnhancedToolbarProps {
    editor: Editor;
}

export function EnhancedToolbar({ editor }: EnhancedToolbarProps) {
    return (
        <div className="flex flex-wrap items-center gap-1 p-2 border-b border-gray-100">
            {/* 标题 */}
            <div className="flex items-center gap-0.5 mr-1">
                <Button
                    variant={editor.isActive("heading", { level: 1 }) ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    className={`h-8 px-2 ${editor.isActive("heading", { level: 1 }) ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="标题 1"
                >
                    <TextHOne size={18} />
                </Button>
                <Button
                    variant={editor.isActive("heading", { level: 2 }) ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    className={`h-8 px-2 ${editor.isActive("heading", { level: 2 }) ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="标题 2"
                >
                    <TextHTwo size={18} />
                </Button>
                <Button
                    variant={editor.isActive("heading", { level: 3 }) ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                    className={`h-8 px-2 ${editor.isActive("heading", { level: 3 }) ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="标题 3"
                >
                    <TextHThree size={18} />
                </Button>
            </div>

            <div className="h-6 w-px bg-gray-200" />

            {/* 格式化 */}
            <div className="flex items-center gap-0.5 mx-1">
                <Button
                    variant={editor.isActive("bold") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    className={`h-8 px-2 ${editor.isActive("bold") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="粗体"
                >
                    <TextBolder size={18} weight="bold" />
                </Button>
                <Button
                    variant={editor.isActive("italic") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    className={`h-8 px-2 ${editor.isActive("italic") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="斜体"
                >
                    <TextItalic size={18} />
                </Button>
                <Button
                    variant={editor.isActive("strike") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                    className={`h-8 px-2 ${editor.isActive("strike") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="删除线"
                >
                    <TextStrikethrough size={18} />
                </Button>
            </div>

            <div className="h-6 w-px bg-gray-200" />

            {/* 列表 */}
            <div className="flex items-center gap-0.5 mx-1">
                <Button
                    variant={editor.isActive("bulletList") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={`h-8 px-2 ${editor.isActive("bulletList") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="无序列表"
                >
                    <ListBullets size={18} />
                </Button>
                <Button
                    variant={editor.isActive("orderedList") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={`h-8 px-2 ${editor.isActive("orderedList") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="有序列表"
                >
                    <ListNumbers size={18} />
                </Button>
            </div>

            <div className="h-6 w-px bg-gray-200" />

            {/* 其他 */}
            <div className="flex items-center gap-0.5 mx-1">
                <Button
                    variant={editor.isActive("blockquote") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleBlockquote().run()}
                    className={`h-8 px-2 ${editor.isActive("blockquote") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="引用"
                >
                    <Quotes size={18} />
                </Button>
                <Button
                    variant={editor.isActive("codeBlock") ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                    className={`h-8 px-2 ${editor.isActive("codeBlock") ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100"}`}
                    title="代码块"
                >
                    <Code size={18} />
                </Button>
            </div>
        </div>
    );
}
