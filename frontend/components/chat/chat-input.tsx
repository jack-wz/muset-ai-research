"use client";

import React from "react";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
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
    <div className="border-t border-gray-200 p-4">
      <div className="relative">
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Drop an idea, let's shape..."
          className="min-h-[80px] pr-24 resize-none"
          disabled={isLoading}
        />

        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          <Button variant="ghost" size="icon" title="Attach file">
            <Paperclip size={20} />
          </Button>

          <Button variant="ghost" size="icon" title="Attach image">
            <ImageIcon size={20} />
          </Button>

          <Button
            variant="primary"
            size="icon"
            onClick={onSend}
            disabled={isLoading || !value.trim()}
            title="Send message"
          >
            <PaperPlaneTilt size={20} weight="fill" />
          </Button>
        </div>
      </div>

      <div className="mt-2 text-xs text-gray-500">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
}
