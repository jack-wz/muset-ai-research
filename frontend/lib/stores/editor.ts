import { create } from "zustand";
import type { Editor, JSONContent } from "@tiptap/react";

interface EditorState {
  editor: Editor | null;
  content: JSONContent | null;
  isSaving: boolean;
  lastSaved: Date | null;
  selectedText: string;
  selectionRange: { from: number; to: number } | null;

  setEditor: (editor: Editor | null) => void;
  setContent: (content: JSONContent) => void;
  setSaving: (saving: boolean) => void;
  setLastSaved: (date: Date) => void;
  setSelection: (text: string, range: { from: number; to: number } | null) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  editor: null,
  content: null,
  isSaving: false,
  lastSaved: null,
  selectedText: "",
  selectionRange: null,

  setEditor: (editor) => set({ editor }),
  setContent: (content) => set({ content }),
  setSaving: (saving) => set({ isSaving: saving }),
  setLastSaved: (date) => set({ lastSaved: date }),
  setSelection: (text, range) => set({ selectedText: text, selectionRange: range }),
}));
