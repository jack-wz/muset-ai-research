"use client";

import { useEffect, useState } from "react";

/**
 * Global search hook with keyboard shortcut support
 * Handles Cmd+K (Mac) and Ctrl+K (Windows/Linux) to open search modal
 */
export function useGlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    // Add event listener
    window.addEventListener("keydown", handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const openSearch = () => setIsOpen(true);
  const closeSearch = () => setIsOpen(false);
  const toggleSearch = () => setIsOpen((prev) => !prev);

  return {
    isOpen,
    openSearch,
    closeSearch,
    toggleSearch,
  };
}
