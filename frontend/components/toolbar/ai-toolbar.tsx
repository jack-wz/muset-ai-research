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
import { DiffViewer } from "../editor/diff-viewer";

interface AIToolbarProps {
  editor: Editor;
  workspaceId: string;
  projectId: string;
  onClose: () => void;
}

type AIAction = "continue" | "summarize" | "polish" | "translate" | "expand";

interface DiffState {
  originalText: string;
  modifiedText: string;
  action: AIAction;
  from: number;
  to: number;
}

export function AIToolbar({ editor, workspaceId, projectId, onClose }: AIToolbarProps) {
  const [isLoading, setIsLoading] = React.useState(false);
  const [diffState, setDiffState] = React.useState<DiffState | null>(null);

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

      // Show diff viewer instead of immediately applying changes
      setDiffState({
        originalText: selectedText,
        modifiedText: fullResponse,
        action,
        from,
        to,
      });
    } catch (error) {
      console.error("AI action failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccept = () => {
    if (!diffState) return;

    const { action, from, to, modifiedText } = diffState;

    // Apply the changes
    if (action === "continue") {
      editor.chain().focus().insertContentAt(to, modifiedText).run();
    } else {
      // Replace selected text for other actions
      editor.chain().focus().deleteRange({ from, to }).insertContentAt(from, modifiedText).run();
    }

    setDiffState(null);
    onClose();
  };

  const handleReject = () => {
    setDiffState(null);
  };

  // Show diff viewer if we have AI suggestions
  if (diffState) {
    return (
      <DiffViewer
        originalText={diffState.originalText}
        modifiedText={diffState.modifiedText}
        onAccept={handleAccept}
        onReject={handleReject}
      />
    );
  }

  return (
    <Card className="flex items-center gap-2 p-2 shadow-lg">
      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("continue")}
        title="Continue writing"
      >
        <PencilSimple size={18} weight="fill" />
        {isLoading ? "Loading..." : "Continue"}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("summarize")}
        title="Summarize"
      >
        <ArrowsClockwise size={18} weight="fill" />
        {isLoading ? "Loading..." : "Summarize"}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("polish")}
        title="Polish"
      >
        <TextAa size={18} weight="fill" />
        {isLoading ? "Loading..." : "Polish"}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("translate")}
        title="Translate"
      >
        <Translate size={18} weight="fill" />
        {isLoading ? "Loading..." : "Translate"}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        disabled={isLoading}
        onClick={() => handleAIAction("expand")}
        title="Expand"
      >
        <ArrowsOutSimple size={18} weight="fill" />
        {isLoading ? "Loading..." : "Expand"}
      </Button>

      <div className="mx-1 h-6 w-px bg-gray-300" />

      <Button variant="ghost" size="icon" onClick={onClose} disabled={isLoading}>
        <X size={18} />
      </Button>
    </Card>
  );
}
