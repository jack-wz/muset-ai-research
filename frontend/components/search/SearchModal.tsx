"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { searchAPI, SearchResultItem, SearchHistoryItem } from "@/lib/api/search";
import SearchInput from "./SearchInput";
import SearchResults from "./SearchResults";
import SearchHistory from "./SearchHistory";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string;
}

export default function SearchModal({
  isOpen,
  onClose,
  workspaceId,
}: SearchModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [contentTypeFilter, setContentTypeFilter] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(true);
  const modalRef = useRef<HTMLDivElement>(null);

  // Load search history on mount
  useEffect(() => {
    if (isOpen && workspaceId) {
      loadHistory();
    }
  }, [isOpen, workspaceId]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
      setShowHistory(true);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "Escape":
          onClose();
          break;
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case "Enter":
          e.preventDefault();
          if (results[selectedIndex]) {
            handleResultClick(results[selectedIndex]);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, results, selectedIndex, onClose]);

  // Load search history
  const loadHistory = async () => {
    try {
      const response = await searchAPI.getHistory(workspaceId);
      setHistory(response.history);
    } catch (error) {
      console.error("Failed to load search history:", error);
    }
  };

  // Perform search
  const performSearch = useCallback(
    async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        setShowHistory(true);
        return;
      }

      setLoading(true);
      setShowHistory(false);

      try {
        const response = await searchAPI.search(workspaceId, {
          query: searchQuery,
          content_types: contentTypeFilter.length > 0 ? contentTypeFilter : undefined,
          limit: 20,
          offset: 0,
        });

        setResults(response.results);
        setTotalResults(response.total);
        setSelectedIndex(0);
      } catch (error) {
        console.error("Search failed:", error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [workspaceId, contentTypeFilter]
  );

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        performSearch(query);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, performSearch]);

  // Handle result click
  const handleResultClick = (result: SearchResultItem) => {
    // Navigate to the result
    if (result.url) {
      window.location.href = result.url;
    }
    onClose();
  };

  // Handle history item click
  const handleHistoryClick = (item: SearchHistoryItem) => {
    setQuery(item.query);
    setShowHistory(false);
  };

  // Handle content type filter toggle
  const toggleContentType = (type: string) => {
    setContentTypeFilter((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  // Handle click outside modal
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black bg-opacity-50 pt-20">
      <div
        ref={modalRef}
        className="w-full max-w-2xl rounded-lg bg-white shadow-2xl dark:bg-gray-800"
      >
        {/* Search Input */}
        <SearchInput
          value={query}
          onChange={setQuery}
          loading={loading}
          contentTypeFilter={contentTypeFilter}
          onToggleContentType={toggleContentType}
        />

        {/* Results or History */}
        <div className="max-h-96 overflow-y-auto">
          {showHistory && history.length > 0 ? (
            <SearchHistory history={history} onHistoryClick={handleHistoryClick} />
          ) : (
            <SearchResults
              results={results}
              selectedIndex={selectedIndex}
              onResultClick={handleResultClick}
              loading={loading}
              query={query}
              totalResults={totalResults}
            />
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-3 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex gap-2">
              <kbd className="rounded border border-gray-300 px-2 py-1 dark:border-gray-600">
                ↑↓
              </kbd>
              <span>Navigate</span>
              <kbd className="rounded border border-gray-300 px-2 py-1 dark:border-gray-600">
                Enter
              </kbd>
              <span>Select</span>
              <kbd className="rounded border border-gray-300 px-2 py-1 dark:border-gray-600">
                Esc
              </kbd>
              <span>Close</span>
            </div>
            {!showHistory && (
              <span>
                {totalResults} {totalResults === 1 ? "result" : "results"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
