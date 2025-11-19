"use client";

import { SearchHistoryItem } from "@/lib/api/search";

interface SearchHistoryProps {
  history: SearchHistoryItem[];
  onHistoryClick: (item: SearchHistoryItem) => void;
}

// Helper function to format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
  }
  const days = Math.floor(diffInSeconds / 86400);
  return `${days} ${days === 1 ? "day" : "days"} ago`;
}

export default function SearchHistory({
  history,
  onHistoryClick,
}: SearchHistoryProps) {
  if (history.length === 0) {
    return (
      <div className="py-12 text-center">
        <svg
          className="mx-auto mb-3 h-12 w-12 text-gray-300 dark:text-gray-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No search history yet
        </p>
      </div>
    );
  }

  return (
    <div className="py-2">
      <div className="px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          Recent Searches
        </h3>
      </div>

      {history.map((item) => (
        <button
          key={item.id}
          onClick={() => onHistoryClick(item)}
          className="w-full px-4 py-2.5 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <div className="flex items-center gap-3">
            {/* Clock icon */}
            <div className="text-gray-400">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>

            {/* Query */}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
                {item.query}
              </p>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span>{formatRelativeTime(item.created_at)}</span>
                {item.results_count?.total !== undefined && (
                  <>
                    <span>•</span>
                    <span>
                      {item.results_count.total}{" "}
                      {item.results_count.total === 1 ? "result" : "results"}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex-shrink-0 text-gray-400">
              <svg
                className="h-4 w-4"
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
          </div>
        </button>
      ))}
    </div>
  );
}
