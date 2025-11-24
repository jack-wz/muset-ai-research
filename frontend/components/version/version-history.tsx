"use client";
// Force rebuild

import React from "react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { ClockCounterClockwise, ArrowCounterClockwise, X } from "phosphor-react";
import { formatRelativeTime } from "@/lib/utils";

interface Version {
  id: string;
  version: number;
  content: unknown;
  created_at: string;
  created_by: string;
  description?: string;
}

interface VersionHistoryProps {
  projectId: string;
  onRestore: (version: Version) => void;
  onClose?: () => void;
}

export function VersionHistory({ projectId, onRestore, onClose }: VersionHistoryProps) {
  const [versions, setVersions] = React.useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = React.useState<Version | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    loadVersions();
  }, [projectId]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      // TODO: Fetch versions from API
      // For now, using mock data
      setVersions([
        {
          id: "v1",
          version: 1,
          content: {},
          created_at: new Date(Date.now() - 3600000).toISOString(),
          created_by: "You",
          description: "Initial version",
        },
        {
          id: "v2",
          version: 2,
          content: {},
          created_at: new Date(Date.now() - 1800000).toISOString(),
          created_by: "You",
          description: "Added introduction",
        },
        {
          id: "v3",
          version: 3,
          content: {},
          created_at: new Date().toISOString(),
          created_by: "You",
          description: "Current version",
        },
      ]);
    } catch (error) {
      console.error("Failed to load versions:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = (version: Version) => {
    if (confirm(`Are you sure you want to restore to version ${version.version}?`)) {
      onRestore(version);
    }
  };

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex items-center justify-between border-b border-gray-200 p-4">
        <div className="flex items-center gap-2">
          <ClockCounterClockwise size={24} weight="fill" />
          <h2 className="text-lg font-semibold">Version History</h2>
        </div>
        {onClose && (
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X size={20} />
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="text-center text-gray-500">Loading versions...</div>
        ) : versions.length === 0 ? (
          <div className="text-center text-gray-500">
            No version history available. Make some changes to see them here.
          </div>
        ) : (
          <div className="space-y-3">
            {versions.map((version) => (
              <Card
                key={version.id}
                className={`cursor-pointer p-4 transition-shadow hover:shadow-md ${selectedVersion?.id === version.id ? "border-blue-500" : ""
                  }`}
                onClick={() => setSelectedVersion(version)}
              >
                <div className="mb-2 flex items-start justify-between">
                  <div>
                    <div className="font-semibold">Version {version.version}</div>
                    <div className="text-sm text-gray-600">{version.description}</div>
                  </div>
                  {version.version < versions.length && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRestore(version);
                      }}
                    >
                      <ArrowCounterClockwise size={16} />
                      Restore
                    </Button>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{version.created_by}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(version.created_at)}</span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {selectedVersion && (
        <div className="border-t border-gray-200 p-4">
          <h3 className="mb-2 font-semibold">Version {selectedVersion.version}</h3>
          <p className="text-sm text-gray-600">
            Click &quot;Restore&quot; to restore this version. The current version will be saved before
            restoring.
          </p>
        </div>
      )}
    </div>
  );
}
