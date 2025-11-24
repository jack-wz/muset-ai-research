/**
 * API Client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
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

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let url = `${this.baseUrl}${endpoint}`;
    if (options.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const separator = url.includes("?") ? "&" : "?";
      url += `${separator}${searchParams.toString()}`;
    }



    const response = await fetch(url, {
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
        console.error('API Error data:', errorData);
        error.message = errorData.message || errorData.detail || error.message;
        error.code = errorData.code;
      } catch {
        // If response is not JSON, use statusText
      }

      throw error;
    }

    return response.json();
  }

  public async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  public async post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public async put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async register(name: string, email: string, password: string) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
  }

  async getCurrentUser() {
    return this.request("/auth/me");
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
    data: { title?: string; content?: unknown }
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
