"use client";

import React from "react";
import { Button } from "../ui/button";
import { Paperclip, Image as ImageIcon, PaperPlaneTilt } from "phosphor-react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
}

export function ChatInput({ value, onChange, onSend, isLoading }: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="p-4">
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="说说你的想法，一起完善..."
          className="w-full min-h-[100px] max-h-[200px] px-4 py-3 pr-32 bg-transparent border-0 focus:outline-none resize-none text-gray-900 placeholder:text-gray-400"
          disabled={isLoading}
        />

        <div className="absolute bottom-3 right-3 flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            title="附加文件"
          >
            <Paperclip size={18} />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            title="附加图片"
          >
            <ImageIcon size={18} />
          </Button>

          <Button
            size="icon"
            onClick={onSend}
            disabled={isLoading || !value.trim()}
            className="h-8 w-8 bg-gradient-to-br from-primary to-secondary hover:from-primary-hover hover:to-secondary text-white shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            title="发送消息"
          >
            <PaperPlaneTilt size={18} weight="fill" />
          </Button>
        </div>
      </div>

      <div className="mt-2 text-xs text-gray-400 px-1">
        按 <kbd className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-mono text-xs">Enter</kbd> 发送，<kbd className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-mono text-xs">Shift+Enter</kbd> 换行
      </div>
    </div>
  );
}
