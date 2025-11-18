"use client";

import React from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { useEditorStore } from "@/lib/stores/editor";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { apiClient } from "@/lib/api/client";
import { EditorToolbar } from "./editor-toolbar";
import { AIToolbar } from "../toolbar/ai-toolbar";

interface RichTextEditorProps {
  workspaceId: string;
  projectId: string;
  initialContent?: any;
}

export function RichTextEditor({
  workspaceId,
  projectId,
  initialContent,
}: RichTextEditorProps) {
  const { setEditor, setContent, setSaving, setLastSaved, setSelection } = useEditorStore();
  const { updateProject } = useWorkspaceStore();
  const [showAIToolbar, setShowAIToolbar] = React.useState(false);
  const [toolbarPosition, setToolbarPosition] = React.useState({ top: 0, left: 0 });

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: "Start writing or press '/' for commands...",
      }),
    ],
    content: initialContent,
    onUpdate: ({ editor }) => {
      const json = editor.getJSON();
      setContent(json);
      debouncedSave(json);
    },
    onSelectionUpdate: ({ editor }) => {
      const { from, to } = editor.state.selection;
      const text = editor.state.doc.textBetween(from, to, " ");

      if (text.length > 0) {
        setSelection(text, { from, to });
        // Show AI toolbar when text is selected
        const coords = editor.view.coordsAtPos(from);
        setToolbarPosition({ top: coords.top - 50, left: coords.left });
        setShowAIToolbar(true);
      } else {
        setSelection("", null);
        setShowAIToolbar(false);
      }
    },
  });

  React.useEffect(() => {
    if (editor) {
      setEditor(editor);
    }
    return () => {
      setEditor(null);
    };
  }, [editor, setEditor]);

  const saveContent = React.useCallback(
    async (content: any) => {
      try {
        setSaving(true);
        await apiClient.updateProject(workspaceId, projectId, { content });
        updateProject(projectId, { content });
        setLastSaved(new Date());
      } catch (error) {
        console.error("Failed to save content:", error);
      } finally {
        setSaving(false);
      }
    },
    [workspaceId, projectId, setSaving, setLastSaved, updateProject]
  );

  const debouncedSave = React.useMemo(
    () => debounce(saveContent, 1000),
    [saveContent]
  );

  if (!editor) {
    return null;
  }

  return (
    <div className="relative flex h-full flex-col">
      <EditorToolbar editor={editor} />

      <div className="prose prose-lg max-w-none flex-1 overflow-auto p-8">
        <EditorContent editor={editor} />
      </div>

      {showAIToolbar && (
        <div
          style={{
            position: "fixed",
            top: toolbarPosition.top,
            left: toolbarPosition.left,
          }}
        >
          <AIToolbar
            editor={editor}
            workspaceId={workspaceId}
            projectId={projectId}
            onClose={() => setShowAIToolbar(false)}
          />
        </div>
      )}
    </div>
  );
}

// Debounce utility
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
