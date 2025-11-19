/**
 * Notifications API client
 */

import { apiClient } from "./client";

export interface Notification {
  id: string;
  user_id: string;
  workspace_id?: string;
  type: "info" | "success" | "warning" | "error" | "mention" | "task_complete" | "quota_low" | "subscription_expire";
  title: string;
  message: string;
  data: Record<string, any>;
  action_url?: string;
  action_label?: string;
  read: boolean;
  read_at?: string;
  delivered: boolean;
  delivered_at?: string;
  email_sent: boolean;
  email_sent_at?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  email_enabled: boolean;
  in_app_enabled: boolean;
  desktop_enabled: boolean;
  type_preferences: Record<string, any>;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  created_at: string;
  updated_at: string;
}

export class NotificationsAPI {
  /**
   * Get user notifications
   */
  async getNotifications(params?: {
    read?: boolean;
    type?: string;
    limit?: number;
    offset?: number;
  }): Promise<NotificationListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.read !== undefined) queryParams.append("read", String(params.read));
    if (params?.type) queryParams.append("type", params.type);
    if (params?.limit) queryParams.append("limit", String(params.limit));
    if (params?.offset) queryParams.append("offset", String(params.offset));

    return apiClient.request(`/notifications?${queryParams.toString()}`);
  }

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<{ count: number }> {
    return apiClient.request("/notifications/unread-count");
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<Notification> {
    return apiClient.request(`/notifications/${notificationId}/read`, {
      method: "POST",
    });
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<{ success: boolean; message: string; count: number }> {
    return apiClient.request("/notifications/read-all", {
      method: "POST",
    });
  }

  /**
   * Delete notification
   */
  async deleteNotification(notificationId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.request(`/notifications/${notificationId}`, {
      method: "DELETE",
    });
  }

  /**
   * Get notification preferences
   */
  async getPreferences(): Promise<NotificationPreference> {
    return apiClient.request("/notifications/preferences");
  }

  /**
   * Update notification preferences
   */
  async updatePreferences(preferences: Partial<NotificationPreference>): Promise<NotificationPreference> {
    return apiClient.request("/notifications/preferences", {
      method: "PATCH",
      body: JSON.stringify(preferences),
    });
  }

  /**
   * Connect to WebSocket for real-time notifications
   */
  connectWebSocket(token: string, onMessage: (notification: Notification) => void): WebSocket {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/notifications/ws";
    const ws = new WebSocket(`${wsUrl}?token=${token}`);

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.event === "notification") {
          onMessage(message.data);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    // Send periodic ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000); // 30 seconds

    ws.onclose = () => {
      clearInterval(pingInterval);
    };

    return ws;
  }
}

export const notificationsAPI = new NotificationsAPI();
