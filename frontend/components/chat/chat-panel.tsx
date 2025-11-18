"use client";

import React from "react";
import { Button } from "../ui/button";
import { X, Paperclip, Image as ImageIcon, PaperPlaneTilt } from "phosphor-react";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { apiClient } from "@/lib/api/client";
import { useWorkspaceStore } from "@/lib/stores/workspace";

interface ChatPanelProps {
  workspaceId: string;
  onClose: () => void;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export function ChatPanel({ workspaceId, onClose }: ChatPanelProps) {
  const { currentProject } = useWorkspaceStore();
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !currentProject) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      for await (const chunk of apiClient.streamChat(
        workspaceId,
        currentProject.id,
        input
      )) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      }

      // Mark streaming as complete
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id ? { ...msg, isStreaming: false } : msg
        )
      );
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, content: "Sorry, an error occurred.", isStreaming: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="flex w-96 flex-col border-l border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-4">
        <h2 className="text-lg font-semibold">Chat</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X size={20} />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 text-4xl">✨</div>
            <p className="mb-2 text-lg font-medium">Muset thinks with you</p>
            <p className="text-sm text-gray-500">
              Drop an idea, let's shape it together...
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        isLoading={isLoading}
      />
    </aside>
  );
}
