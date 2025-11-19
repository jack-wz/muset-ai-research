/**
 * API Client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

export class APIClient {
  private baseUrl: string;
  private getToken: () => string | null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Get token from localStorage or cookie
    this.getToken = () => {
      if (typeof window !== "undefined") {
        return localStorage.getItem("auth_token");
      }
      return null;
    };
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = {
        message: response.statusText,
        status: response.status,
      };

      try {
        const errorData = await response.json();
        error.message = errorData.message || errorData.detail || error.message;
        error.code = errorData.code;
      } catch {
        // If response is not JSON, use statusText
      }

      throw error;
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request("/auth/logout", { method: "POST" });
  }

  // Workspace endpoints
  async getWorkspaces() {
    return this.request("/workspaces");
  }

  async getWorkspace(id: string) {
    return this.request(`/workspaces/${id}`);
  }

  async createWorkspace(data: { name: string; description?: string }) {
    return this.request("/workspaces", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Project endpoints
  async getProjects(workspaceId: string) {
    return this.request(`/workspaces/${workspaceId}/projects`);
  }

  async getProject(workspaceId: string, projectId: string) {
    return this.request(`/workspaces/${workspaceId}/projects/${projectId}`);
  }

  async createProject(workspaceId: string, data: { title: string }) {
    return this.request(`/workspaces/${workspaceId}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProject(
    workspaceId: string,
    projectId: string,
    data: { title?: string; content?: any }
  ) {
    return this.request(`/workspaces/${workspaceId}/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Chat endpoints
  async sendMessage(
    workspaceId: string,
    projectId: string,
    message: string,
    files?: File[]
  ) {
    const formData = new FormData();
    formData.append("message", message);
    if (files) {
      files.forEach((file) => formData.append("files", file));
    }

    return fetch(
      `${this.baseUrl}/workspaces/${workspaceId}/projects/${projectId}/chat`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: formData,
      }
    );
  }

  // Stream chat response
  async *streamChat(
    workspaceId: string,
    projectId: string,
    message: string
  ): AsyncGenerator<string> {
    const response = await this.sendMessage(workspaceId, projectId, message);

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") return;
          try {
            const parsed = JSON.parse(data);
            yield parsed.content || "";
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  }

  // File endpoints
  async getFiles(workspaceId: string) {
    return this.request(`/workspaces/${workspaceId}/files`);
  }

  async uploadFile(workspaceId: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);

    return fetch(`${this.baseUrl}/workspaces/${workspaceId}/files`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
      body: formData,
    });
  }
}

export const apiClient = new APIClient();
