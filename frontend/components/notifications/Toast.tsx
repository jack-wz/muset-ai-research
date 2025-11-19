"use client";

import { useEffect } from "react";
import { Notification } from "@/lib/api/notifications";

interface ToastProps {
  notification: Notification;
  onClose: () => void;
  onAction?: () => void;
}

export default function Toast({ notification, onClose, onAction }: ToastProps) {
  // Auto-dismiss after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  // Get color scheme based on type
  const getColorClass = () => {
    switch (notification.type) {
      case "success":
        return "bg-green-50 border-green-200 text-green-900 dark:bg-green-900 dark:border-green-700 dark:text-green-100";
      case "warning":
        return "bg-yellow-50 border-yellow-200 text-yellow-900 dark:bg-yellow-900 dark:border-yellow-700 dark:text-yellow-100";
      case "error":
        return "bg-red-50 border-red-200 text-red-900 dark:bg-red-900 dark:border-red-700 dark:text-red-100";
      default:
        return "bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100";
    }
  };

  // Get icon based on type
  const getIcon = () => {
    switch (notification.type) {
      case "success":
        return "✅";
      case "warning":
        return "⚠️";
      case "error":
        return "❌";
      case "mention":
        return "👤";
      case "task_complete":
        return "✨";
      default:
        return "ℹ️";
    }
  };

  return (
    <div
      className={`pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border shadow-lg ${getColorClass()}`}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0 text-2xl">{getIcon()}</div>
          <div className="ml-3 w-0 flex-1">
            <p className="text-sm font-medium">{notification.title}</p>
            <p className="mt-1 text-sm opacity-90">{notification.message}</p>
            {notification.action_url && notification.action_label && (
              <div className="mt-3 flex gap-2">
                <button
                  onClick={onAction}
                  className="text-sm font-medium underline hover:no-underline"
                >
                  {notification.action_label}
                </button>
              </div>
            )}
          </div>
          <div className="ml-4 flex flex-shrink-0">
            <button
              onClick={onClose}
              className="inline-flex rounded-md p-1.5 hover:bg-black hover:bg-opacity-10 focus:outline-none"
            >
              <span className="sr-only">Close</span>
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
