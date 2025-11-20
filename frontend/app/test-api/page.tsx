"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api/client";

export default function TestApiPage() {
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const testLogin = async () => {
    setLoading(true);
    setResult("Testing login...");
    try {
      const response: any = await apiClient.login("demo@muset.ai", "demo123");
      setResult(JSON.stringify(response, null, 2));
      
      if (response.access_token) {
        localStorage.setItem("auth_token", response.access_token);
        setResult(prev => prev + "\n\nToken saved! Testing getCurrentUser...");
        
        const user = await apiClient.getCurrentUser();
        setResult(prev => prev + "\n\nUser: " + JSON.stringify(user, null, 2));
        
        setResult(prev => prev + "\n\nTesting createWorkspace...");
        const workspace = await apiClient.createWorkspace({
          name: "Test Workspace from API Test",
        });
        setResult(prev => prev + "\n\nWorkspace: " + JSON.stringify(workspace, null, 2));
      }
    } catch (error: any) {
      setResult("Error: " + JSON.stringify(error, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const testGetWorkspaces = async () => {
    setLoading(true);
    setResult("Testing getWorkspaces...");
    try {
      const workspaces = await apiClient.getWorkspaces();
      setResult(JSON.stringify(workspaces, null, 2));
    } catch (error: any) {
      setResult("Error: " + JSON.stringify(error, null, 2));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>
      
      <div className="space-x-4 mb-4">
        <button
          onClick={testLogin}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Test Full Flow (Login + Create Workspace)
        </button>
        
        <button
          onClick={testGetWorkspaces}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          Test Get Workspaces
        </button>
      </div>

      <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
        {result || "Click a button to test"}
      </pre>
    </div>
  );
}
