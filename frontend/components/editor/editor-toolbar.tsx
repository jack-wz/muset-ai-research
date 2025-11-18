"use client";

import React from "react";
import type { Editor } from "@tiptap/react";
import { Button } from "../ui/button";
import {
  TextB,
  TextItalic,
  TextStrikethrough,
  ListBullets,
  ListNumbers,
  Quotes,
  Code,
} from "phosphor-react";

interface EditorToolbarProps {
  editor: Editor;
}

export function EditorToolbar({ editor }: EditorToolbarProps) {
  return (
    <div className="flex items-center gap-1 border-b border-gray-200 bg-white p-2">
      <Button
        variant={editor.isActive("bold") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <TextB size={20} />
      </Button>

      <Button
        variant={editor.isActive("italic") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <TextItalic size={20} />
      </Button>

      <Button
        variant={editor.isActive("strike") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleStrike().run()}
      >
        <TextStrikethrough size={20} />
      </Button>

      <div className="mx-2 h-6 w-px bg-gray-300" />

      <Button
        variant={editor.isActive("bulletList") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        <ListBullets size={20} />
      </Button>

      <Button
        variant={editor.isActive("orderedList") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      >
        <ListNumbers size={20} />
      </Button>

      <div className="mx-2 h-6 w-px bg-gray-300" />

      <Button
        variant={editor.isActive("blockquote") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      >
        <Quotes size={20} />
      </Button>

      <Button
        variant={editor.isActive("codeBlock") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
      >
        <Code size={20} />
      </Button>
    </div>
  );
}
