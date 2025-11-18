"use client";

import React from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { File, Folder, X } from "phosphor-react";
import { apiClient } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";

interface FileItem {
  id: string;
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  modified: string;
}

interface FileNavigatorProps {
  workspaceId: string;
  onClose?: () => void;
}

export function FileNavigator({ workspaceId, onClose }: FileNavigatorProps) {
  const [files, setFiles] = React.useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = React.useState<FileItem | null>(null);
  const [fileContent, setFileContent] = React.useState<string>("");
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    loadFiles();
  }, [workspaceId]);

  const loadFiles = async () => {
    try {
      setIsLoading(true);
      const data: any = await apiClient.getFiles(workspaceId);
      setFiles(data);
    } catch (error) {
      console.error("Failed to load files:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileClick = async (file: FileItem) => {
    if (file.type === "directory") return;

    setSelectedFile(file);
    try {
      // Fetch file content
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/files/${file.id}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );
      const content = await response.text();
      setFileContent(content);
    } catch (error) {
      console.error("Failed to load file content:", error);
    }
  };

  return (
    <div className="flex h-full">
      {/* File List */}
      <div className="w-64 border-r border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="font-semibold">Files</h2>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X size={20} />
            </Button>
          )}
        </div>

        <div className="overflow-auto p-2">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-gray-500">Loading...</div>
          ) : files.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">No files yet</div>
          ) : (
            files.map((file) => (
              <button
                key={file.id}
                onClick={() => handleFileClick(file)}
                className={`flex w-full items-center gap-2 rounded-lg p-2 text-left hover:bg-gray-100 ${
                  selectedFile?.id === file.id ? "bg-blue-50" : ""
                }`}
              >
                {file.type === "directory" ? (
                  <Folder size={20} weight="fill" className="text-yellow-500" />
                ) : (
                  <File size={20} weight="fill" className="text-gray-400" />
                )}
                <div className="flex-1 overflow-hidden">
                  <div className="truncate text-sm font-medium">{file.name}</div>
                  <div className="text-xs text-gray-500">
                    {formatRelativeTime(file.modified)}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* File Content */}
      <div className="flex-1 bg-gray-50">
        {selectedFile ? (
          <div className="h-full overflow-auto">
            <div className="border-b border-gray-200 bg-white p-4">
              <h3 className="font-semibold">{selectedFile.name}</h3>
              <p className="text-sm text-gray-500">{selectedFile.path}</p>
            </div>
            <div className="p-4">
              <pre className="rounded-lg bg-white p-4 text-sm">
                <code>{fileContent}</code>
              </pre>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-gray-500">
            Select a file to view its content
          </div>
        )}
      </div>
    </div>
  );
}
