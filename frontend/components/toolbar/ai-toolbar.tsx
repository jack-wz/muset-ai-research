"use client";

import React from "react";
import type { Editor } from "@tiptap/react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import {
  PencilSimple,
  ArrowsClockwise,
  TextAa,
  Translate,
  ArrowsOutSimple,
  X,
} from "phosphor-react";
import { apiClient } from "@/lib/api/client";

interface AIToolbarProps {
  editor: Editor;
  workspaceId: string;
  projectId: string;
  onClose: () => void;
}

type AIAction = "continue" | "summarize" | "polish" | "translate" | "expand";

export function AIToolbar({ editor, workspaceId, projectId, onClose }: AIToolbarProps) {
  const [isLoading, setIsLoading] = React.useState(false);

  const handleAIAction = async (action: AIAction) => {
    try {
      setIsLoading(true);

      const { from, to } = editor.state.selection;
      const selectedText = editor.state.doc.textBetween(from, to, " ");

      let prompt = "";
      switch (action) {
        case "continue":
          prompt = `Continue writing from: "${selectedText}"`;
          break;
        case "summarize":
          prompt = `Summarize the following text: "${selectedText}"`;
          break;
        case "polish":
          prompt = `Polish and improve the following text: "${selectedText}"`;
          break;
        case "translate":
          prompt = `Translate the following text to Chinese: "${selectedText}"`;
          break;
        case "expand":
          prompt = `Expand on the following text with more details: "${selectedText}"`;
          break;
      }

      // Stream the AI response
      let fullResponse = "";
      for await (const chunk of apiClient.streamChat(workspaceId, projectId, prompt)) {
        fullResponse += chunk;
      }

      // Insert the AI response
      if (action === "continue") {
        editor.chain().focus().insertContentAt(to, fullResponse).run();
      } else {
        // Replace selected text for other actions
        editor.chain().focus().deleteRange({ from, to }).insertContentAt(from, fullResponse).run();
      }

      onClose();
    } catch (error) {
      console.error("AI action failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="flex items-center gap-2 p-2 shadow-lg">
      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("continue")}
        title="继续写作"
      >
        <PencilSimple size={18} weight="fill" />
        继续写作
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("summarize")}
        title="总结"
      >
        <ArrowsClockwise size={18} weight="fill" />
        总结
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("polish")}
        title="润色"
      >
        <TextAa size={18} weight="fill" />
        润色
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("translate")}
        title="翻译"
      >
        <Translate size={18} weight="fill" />
        翻译
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("expand")}
        title="扩写"
      >
        <ArrowsOutSimple size={18} weight="fill" />
        扩写
      </Button>

      <div className="mx-1 h-6 w-px bg-gray-300" />

      <Button variant="ghost" size="icon" onClick={onClose}>
        <X size={18} />
      </Button>
    </Card>
  );
}
