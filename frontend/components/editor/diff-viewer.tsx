"use client";

import React from "react";
import * as Diff from "diff";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Check, X } from "phosphor-react";

interface DiffViewerProps {
  originalText: string;
  modifiedText: string;
  onAccept: () => void;
  onReject: () => void;
}

export function DiffViewer({
  originalText,
  modifiedText,
  onAccept,
  onReject,
}: DiffViewerProps) {
  const changes = React.useMemo(() => {
    return Diff.diffWords(originalText, modifiedText);
  }, [originalText, modifiedText]);

  return (
    <Card className="max-w-2xl overflow-hidden shadow-xl">
      <div className="border-b bg-gray-50 px-4 py-2">
        <h3 className="text-sm font-semibold text-gray-700">AI Suggestion</h3>
      </div>

      <div className="max-h-96 overflow-y-auto p-4">
        <div className="rounded-lg bg-white font-mono text-sm leading-relaxed">
          {changes.map((part, index) => {
            if (part.added) {
              return (
                <span
                  key={index}
                  className="bg-green-100 text-green-800"
                  title="Added"
                >
                  {part.value}
                </span>
              );
            }
            if (part.removed) {
              return (
                <span
                  key={index}
                  className="bg-red-100 text-red-800 line-through"
                  title="Removed"
                >
                  {part.value}
                </span>
              );
            }
            return (
              <span key={index} className="text-gray-700">
                {part.value}
              </span>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 border-t bg-gray-50 px-4 py-3">
        <Button
          variant="outline"
          size="sm"
          onClick={onReject}
          className="gap-1"
        >
          <X size={16} />
          Reject
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onAccept}
          className="gap-1"
        >
          <Check size={16} />
          Accept
        </Button>
      </div>
    </Card>
  );
}
