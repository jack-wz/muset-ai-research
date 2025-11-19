"use client";

import { useState, useCallback } from "react";
import { Notification } from "@/lib/api/notifications";
import Toast from "./Toast";

export interface ToastNotification extends Notification {
  toastId: string;
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastNotification[]>([]);

  const showToast = useCallback((notification: Notification) => {
    const toastId = `${notification.id}-${Date.now()}`;
    setToasts((prev) => [...prev, { ...notification, toastId }]);
  }, []);

  const removeToast = useCallback((toastId: string) => {
    setToasts((prev) => prev.filter((t) => t.toastId !== toastId));
  }, []);

  const handleAction = useCallback((notification: ToastNotification) => {
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
    removeToast(notification.toastId);
  }, [removeToast]);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <Toast
          key={toast.toastId}
          notification={toast}
          onClose={() => removeToast(toast.toastId)}
          onAction={() => handleAction(toast)}
        />
      ))}
    </div>
  );
}
