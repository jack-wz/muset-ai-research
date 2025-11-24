"use client";

import React from "react";
import { Button } from "../ui/button";
import { X, Sparkle, Lightbulb } from "phosphor-react";
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
            ? { ...msg, content: "抱歉，发生了错误。", isStreaming: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="flex h-full w-full flex-col bg-white/50 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 p-4 bg-white/80">
        <h2 className="text-base font-bold tracking-tight text-gray-900">聊天</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
        >
          <X size={18} />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 scrollbar-hide">
        {messages.length === 0 && (
          <div className="flex h-full flex-col">
            <div className="flex-1 flex flex-col justify-center items-center text-center px-4">
              {/* 欢迎图标 */}
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6366F1]/10 to-[#8B5CF6]/10">
                <Sparkle size={28} className="text-[#6366F1]" weight="fill" />
              </div>

              {/* 欢迎文本 */}
              <p className="mb-2 text-xl font-bold bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] bg-clip-text text-transparent">
                Muset 与你同思
              </p>
              <p className="text-sm text-gray-500 mb-10 max-w-xs">
                说说你的想法，一起完善...
              </p>

              {/* 灵感卡片轮播 */}
              <div className="w-full mb-8">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkle size={14} className="text-[#8B5CF6]" weight="fill" />
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    灵感
                  </span>
                </div>
                <div className="flex overflow-x-auto snap-x snap-mandatory gap-3 pb-3 scrollbar-hide">
                  {[
                    {
                      title: "看看同行在写什么",
                      color: "from-blue-500 to-indigo-600",
                    },
                    {
                      title: "提出一个发人深省的问题",
                      color: "from-purple-500 to-pink-600",
                    },
                    {
                      title: "激发新鲜灵感",
                      color: "from-amber-400 to-orange-500",
                    },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className={`snap-center shrink-0 w-56 h-28 rounded-xl bg-gradient-to-br ${item.color} p-4 text-white flex items-end shadow-md transform transition-all hover:scale-105 hover:shadow-lg cursor-pointer`}
                    >
                      <span className="font-semibold text-base leading-tight">
                        {item.title}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 提示词建议 */}
              <div className="w-full">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb size={14} className="text-yellow-500" weight="fill" />
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    试试这些
                  </span>
                </div>
                <div className="grid gap-2">
                  {[
                    "将「AI 职业转型」改编为适合 Twitter、Medium 和 YouTube 的内容。",
                    "给我 5 个本周的病毒式生活博客主题。",
                    "黄金投资：是还是不是？结合专家趋势分析",
                  ].map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(prompt)}
                      className="text-left p-3 rounded-lg bg-white hover:bg-gray-50 border border-gray-200 hover:border-[#6366F1]/30 transition-all text-sm text-gray-700"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 bg-white/80 p-3">
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            isLoading={isLoading}
          />
        </div>
      </div>
    </aside>
  );
}
