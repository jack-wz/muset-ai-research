"use client";

import { useRef, useEffect } from "react";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  loading: boolean;
  contentTypeFilter: string[];
  onToggleContentType: (type: string) => void;
}

export default function SearchInput({
  value,
  onChange,
  loading,
  contentTypeFilter,
  onToggleContentType,
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const contentTypes = [
    { value: "page", label: "Pages", icon: "📄" },
    { value: "chat_message", label: "Messages", icon: "💬" },
    { value: "file", label: "Files", icon: "📁" },
  ];

  return (
    <div className="p-4">
      {/* Search Input */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          ref={inputRef}
          type="text"
          className="w-full rounded-lg border border-gray-300 bg-white py-3 pl-10 pr-10 text-lg placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-500"
          placeholder="Search pages, messages, files..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        {loading && (
          <div className="absolute inset-y-0 right-3 flex items-center">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500"></div>
          </div>
        )}
      </div>

      {/* Content Type Filters */}
      <div className="mt-3 flex flex-wrap gap-2">
        {contentTypes.map((type) => (
          <button
            key={type.value}
            onClick={() => onToggleContentType(type.value)}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm transition-colors ${
              contentTypeFilter.includes(type.value)
                ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            }`}
          >
            <span>{type.icon}</span>
            <span>{type.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
