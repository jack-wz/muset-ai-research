"use client";

import { SearchResultItem } from "@/lib/api/search";
import SearchResultItemComponent from "./SearchResultItem";

interface SearchResultsProps {
  results: SearchResultItem[];
  selectedIndex: number;
  onResultClick: (result: SearchResultItem) => void;
  loading: boolean;
  query: string;
  totalResults: number;
}

export default function SearchResults({
  results,
  selectedIndex,
  onResultClick,
  loading,
  query,
  totalResults,
}: SearchResultsProps) {
  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Searching...</p>
        </div>
      </div>
    );
  }

  // Show no results message
  if (query && results.length === 0) {
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <p className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
          No results found
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Try adjusting your search or filters
        </p>
      </div>
    );
  }

  // Show results
  return (
    <div className="py-2">
      {results.map((result, index) => (
        <SearchResultItemComponent
          key={result.id}
          result={result}
          isSelected={index === selectedIndex}
          onClick={() => onResultClick(result)}
          query={query}
        />
      ))}
    </div>
  );
}
