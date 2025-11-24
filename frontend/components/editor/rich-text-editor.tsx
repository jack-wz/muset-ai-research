"use client";

import React from "react";
import { useEditor, EditorContent, type JSONContent } from "@tiptap/react";
import { useEditorStore } from "@/lib/stores/editor";
import { useWorkspaceStore } from "@/lib/stores/workspace";
import { apiClient } from "@/lib/api/client";
import { EnhancedToolbar } from "./enhanced-toolbar";
import { SlashCommands } from "./slash-commands";
import { AIToolbar } from "../toolbar/ai-toolbar";
import { getEditorExtensions } from "./extensions";

interface RichTextEditorProps {
  workspaceId: string;
  projectId: string;
  initialContent?: JSONContent;
}

export function RichTextEditor({
  workspaceId,
  projectId,
  initialContent,
}: RichTextEditorProps) {
  const { setEditor, setContent, setSaving, setLastSaved, setSelection } = useEditorStore();
  const { updateProject } = useWorkspaceStore();
  const [showAIToolbar, setShowAIToolbar] = React.useState(false);
  const [showSlashCommands, setShowSlashCommands] = React.useState(false);
  const [toolbarPosition, setToolbarPosition] = React.useState({ top: 0, left: 0 });
  const [slashPosition, setSlashPosition] = React.useState({ top: 0, left: 0 });

  const editor = useEditor({
    extensions: getEditorExtensions(),
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
        setShowSlashCommands(false);
      } else {
        setSelection("", null);
        setShowAIToolbar(false);

        // Check for slash command
        const beforeText = editor.state.doc.textBetween(
          Math.max(0, from - 1),
          from,
          " "
        );
        if (beforeText === "/") {
          const coords = editor.view.coordsAtPos(from);
          setSlashPosition({ top: coords.top + 25, left: coords.left });
          setShowSlashCommands(true);
        } else {
          setShowSlashCommands(false);
        }
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
    async (content: JSONContent) => {
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

  const handleSlashCommandClose = () => {
    setShowSlashCommands(false);
    // Remove the slash character
    if (editor) {
      const { from } = editor.state.selection;
      editor.chain().focus().deleteRange({ from: from - 1, to: from }).run();
    }
  };

  if (!editor) {
    return null;
  }

  return (
    <div className="relative flex h-full flex-col bg-transparent">
      <div className="mx-auto my-6 w-full max-w-4xl flex-1 flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all hover:shadow-md">
        <div className="sticky top-0 z-10 border-b border-gray-100 bg-white/95 backdrop-blur-sm">
          <EnhancedToolbar editor={editor} />
        </div>

        <div className="flex-1 overflow-y-auto p-8 sm:p-16 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
          <EditorContent
            editor={editor}
            className="prose prose-lg max-w-none 
              prose-headings:font-bold prose-headings:text-gray-900
              prose-h1:text-4xl prose-h1:mb-4
              prose-h2:text-3xl prose-h2:mb-3
              prose-h3:text-2xl prose-h3:mb-2
              prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-4
              prose-a:text-primary prose-a:no-underline hover:prose-a:underline
              prose-strong:text-gray-900 prose-strong:font-semibold
              prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
              prose-pre:bg-gray-900 prose-pre:text-gray-100
              prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-4 prose-blockquote:italic
              prose-ul:list-disc prose-ol:list-decimal
              prose-li:text-gray-700
              prose-img:rounded-lg prose-img:shadow-md
              focus:outline-none min-h-[500px]
              [&_.task-list]:list-none [&_.task-list]:pl-0
              [&_.task-item]:flex [&_.task-item]:items-start [&_.task-item]:gap-2
              [&_.tiptap-table]:border-collapse [&_.tiptap-table]:w-full
              [&_.tiptap-table_td]:border [&_.tiptap-table_td]:border-gray-300 [&_.tiptap-table_td]:p-2
              [&_.tiptap-table_th]:border [&_.tiptap-table_th]:border-gray-300 [&_.tiptap-table_th]:p-2 [&_.tiptap-table_th]:bg-gray-100 [&_.tiptap-table_th]:font-semibold
            "
          />
        </div>
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

      {showSlashCommands && (
        <SlashCommands
          editor={editor}
          onClose={handleSlashCommandClose}
          position={slashPosition}
        />
      )}
    </div>
  );
}

// Debounce utility
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
