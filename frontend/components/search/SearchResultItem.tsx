"use client";

import { SearchResultItem } from "@/lib/api/search";
import { useMemo } from "react";

interface SearchResultItemProps {
  result: SearchResultItem;
  isSelected: boolean;
  onClick: () => void;
  query: string;
}

// Helper function to highlight search terms in text
function highlightText(text: string, query: string): React.ReactNode[] {
  if (!query.trim()) return [text];

  const words = query.trim().split(/\s+/);
  const regex = new RegExp(`(${words.join("|")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, index) => {
    const isMatch = regex.test(part);
    return isMatch ? (
      <mark
        key={index}
        className="bg-yellow-200 font-medium text-yellow-900 dark:bg-yellow-800 dark:text-yellow-200"
      >
        {part}
      </mark>
    ) : (
      <span key={index}>{part}</span>
    );
  });
}

// Get icon for content type
function getContentTypeIcon(contentType: string): string {
  switch (contentType) {
    case "page":
      return "📄";
    case "chat_message":
      return "💬";
    case "file":
      return "📁";
    default:
      return "📋";
  }
}

// Get badge color for content type
function getContentTypeBadgeColor(contentType: string): string {
  switch (contentType) {
    case "page":
      return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
    case "chat_message":
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
    case "file":
      return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
  }
}

// Format content type label
function formatContentType(contentType: string): string {
  switch (contentType) {
    case "page":
      return "Page";
    case "chat_message":
      return "Message";
    case "file":
      return "File";
    default:
      return contentType;
  }
}

export default function SearchResultItemComponent({
  result,
  isSelected,
  onClick,
  query,
}: SearchResultItemProps) {
  // Memoize highlighted text
  const highlightedTitle = useMemo(
    () => highlightText(result.title, query),
    [result.title, query]
  );

  const highlightedDescription = useMemo(
    () =>
      result.description ? highlightText(result.description, query) : null,
    [result.description, query]
  );

  return (
    <button
      onClick={onClick}
      className={`w-full px-4 py-3 text-left transition-colors ${
        isSelected
          ? "bg-blue-50 dark:bg-blue-900"
          : "hover:bg-gray-50 dark:hover:bg-gray-700"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="mt-1 text-2xl">
          {getContentTypeIcon(result.content_type)}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Title */}
          <div className="mb-1 flex items-center gap-2">
            <h3 className="truncate text-sm font-medium text-gray-900 dark:text-white">
              {highlightedTitle}
            </h3>
            <span
              className={`flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${getContentTypeBadgeColor(
                result.content_type
              )}`}
            >
              {formatContentType(result.content_type)}
            </span>
          </div>

          {/* Description */}
          {highlightedDescription && (
            <p className="mb-1 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
              {highlightedDescription}
            </p>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
            {/* Tags */}
            {result.metadata.tags && Array.isArray(result.metadata.tags) && (
              <div className="flex gap-1">
                {result.metadata.tags.slice(0, 3).map((tag: string, index: number) => (
                  <span key={index} className="text-gray-500">
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {/* Additional metadata based on content type */}
            {result.content_type === "page" && result.metadata.status && (
              <span className="text-gray-500">• {result.metadata.status}</span>
            )}
            {result.content_type === "chat_message" &&
              result.metadata.session_title && (
                <span className="text-gray-500">
                  • in {result.metadata.session_title}
                </span>
              )}
            {result.content_type === "file" && result.metadata.size && (
              <span className="text-gray-500">
                • {formatFileSize(result.metadata.size)}
              </span>
            )}
          </div>
        </div>

        {/* Arrow indicator for selected */}
        {isSelected && (
          <div className="mt-1 flex-shrink-0 text-blue-500">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        )}
      </div>
    </button>
  );
}

// Helper function to format file size
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1024 * 1024 * 1024)
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + " GB";
}
