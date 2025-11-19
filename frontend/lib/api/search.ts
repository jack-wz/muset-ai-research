/**
 * Search API client
 */

import { apiClient } from "./client";

export interface SearchResultItem {
  id: string;
  content_type: "page" | "chat_message" | "file";
  content_id: string;
  title: string;
  description?: string;
  metadata: Record<string, any>;
  url?: string;
  created_at: string;
  updated_at: string;
}

export interface SearchResponse {
  results: SearchResultItem[];
  total: number;
  limit: number;
  offset: number;
  query: string;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  filters: Record<string, any>;
  results_count: Record<string, any>;
  clicked_result_id?: string;
  created_at: string;
}

export interface SearchHistoryResponse {
  history: SearchHistoryItem[];
  total: number;
}

export interface SearchQuery {
  query: string;
  content_types?: string[];
  limit?: number;
  offset?: number;
}

export class SearchAPI {
  /**
   * Perform search in workspace
   */
  async search(workspaceId: string, query: SearchQuery): Promise<SearchResponse> {
    return apiClient.request(`/search/workspaces/${workspaceId}/search`, {
      method: "POST",
      body: JSON.stringify(query),
    });
  }

  /**
   * Get search history for workspace
   */
  async getHistory(
    workspaceId: string,
    limit: number = 10
  ): Promise<SearchHistoryResponse> {
    return apiClient.request(
      `/search/workspaces/${workspaceId}/search/history?limit=${limit}`
    );
  }

  /**
   * Index specific content
   */
  async indexContent(
    workspaceId: string,
    contentType: string,
    contentId: string
  ): Promise<{ success: boolean; message: string; index_id?: string }> {
    return apiClient.request(`/search/workspaces/${workspaceId}/index`, {
      method: "POST",
      body: JSON.stringify({
        content_type: contentType,
        content_id: contentId,
      }),
    });
  }

  /**
   * Delete search index for content
   */
  async deleteIndex(
    workspaceId: string,
    contentType: string,
    contentId: string
  ): Promise<{ success: boolean; message: string }> {
    return apiClient.request(
      `/search/workspaces/${workspaceId}/index/${contentType}/${contentId}`,
      {
        method: "DELETE",
      }
    );
  }
}

export const searchAPI = new SearchAPI();
