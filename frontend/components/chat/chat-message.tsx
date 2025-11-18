"use client";

import React from "react";
import { formatRelativeTime } from "@/lib/utils";

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
  return (
    <div className={`mb-4 ${message.role === "user" ? "text-right" : ""}`}>
      <div
        className={`inline-block max-w-[80%] rounded-lg px-4 py-2 ${
          message.role === "user"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        <div className="prose prose-sm whitespace-pre-wrap break-words">
          {message.content}
          {message.isStreaming && (
            <span className="inline-block h-4 w-1 animate-pulse bg-current" />
          )}
        </div>
      </div>
      <div className="mt-1 text-xs text-gray-400">
        {formatRelativeTime(message.timestamp)}
      </div>
    </div>
  );
}
