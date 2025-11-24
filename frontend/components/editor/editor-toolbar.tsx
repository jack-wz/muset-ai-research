
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
  TextHTwo
} from "phosphor-react";

interface EditorToolbarProps {
  editor: Editor;
}

export function EditorToolbar({ editor }: EditorToolbarProps) {
  return (
    <div className="flex items-center gap-1 p-2">
      <div className="flex items-center gap-1 mr-2">
        <Button
          variant={editor.isActive("heading", { level: 1 }) ? "secondary" : "ghost"}
          size="sm"
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive("heading", { level: 1 }) ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
        >
          <TextHOne size={18} />
        </Button>
        <Button
          variant={editor.isActive("heading", { level: 2 }) ? "secondary" : "ghost"}
          size="sm"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive("heading", { level: 2 }) ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
        >
          <TextHTwo size={18} />
        </Button>
      </div>

      <div className="h-4 w-px bg-gray-200 mx-1" />

      <Button
        variant={editor.isActive("bold") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={editor.isActive("bold") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <TextBolder size={18} weight="bold" />
      </Button>

      <Button
        variant={editor.isActive("italic") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={editor.isActive("italic") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <TextItalic size={18} />
      </Button>

      <Button
        variant={editor.isActive("strike") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleStrike().run()}
        className={editor.isActive("strike") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <TextStrikethrough size={18} />
      </Button>

      <div className="h-4 w-px bg-gray-200 mx-1" />

      <Button
        variant={editor.isActive("bulletList") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={editor.isActive("bulletList") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <ListBullets size={18} />
      </Button>

      <Button
        variant={editor.isActive("orderedList") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={editor.isActive("orderedList") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <ListNumbers size={18} />
      </Button>

      <div className="h-4 w-px bg-gray-200 mx-1" />

      <Button
        variant={editor.isActive("blockquote") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        className={editor.isActive("blockquote") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <Quotes size={18} />
      </Button>

      <Button
        variant={editor.isActive("codeBlock") ? "secondary" : "ghost"}
        size="sm"
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        className={editor.isActive("codeBlock") ? "bg-primary/10 text-primary" : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}
      >
        <Code size={18} />
      </Button>
    </div>
  );
}
