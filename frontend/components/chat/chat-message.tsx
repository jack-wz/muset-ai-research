"use client";

import React from "react";
import { formatRelativeTime } from "@/lib/utils";
import { User, Sparkle } from "phosphor-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 mb-6 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${isUser
          ? "bg-gradient-to-br from-primary to-secondary text-white shadow-md"
          : "bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-md"
        }`}>
        {isUser ? <User size={16} weight="bold" /> : <Sparkle size={16} weight="fill" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[75%] ${isUser ? "flex flex-col items-end" : ""}`}>
        <div className={`rounded-2xl px-4 py-3 shadow-sm ${isUser
            ? "bg-gradient-to-br from-primary to-primary/90 text-white"
            : "bg-white border border-gray-100"
          }`}>
          <div className={`prose prose-sm max-w-none ${isUser ? "prose-invert" : "prose-gray"
            }`}>
            <div className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
              {message.isStreaming && (
                <span className="inline-block ml-1 h-4 w-0.5 animate-pulse bg-current" />
              )}
            </div>
          </div>
        </div>

        <div className={`mt-1.5 text-xs text-gray-400 ${isUser ? "text-right" : ""}`}>
          {formatRelativeTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}
