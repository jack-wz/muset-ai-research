"use client";

import React, { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api/client";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const code = searchParams.get("code");
      const error = searchParams.get("error");

      if (error) {
        console.error("OAuth error:", error);
        router.push("/login?error=" + encodeURIComponent(error));
        return;
      }

      if (!code) {
        router.push("/login");
        return;
      }

      try {
        // Exchange code for token
        const response = await apiClient.post<{ access_token: string }>(
          "/auth/google/callback",
          { code }
        );

        if (response.access_token) {
          localStorage.setItem("auth_token", response.access_token);
          // Redirect to workspace
          router.push("/workspace");
        }
      } catch (err: any) {
        console.error("Callback error:", err);
        router.push("/login?error=" + encodeURIComponent("Authentication failed"));
      }
    };

    handleOAuthCallback();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4 flex justify-center">
          <svg
            className="h-12 w-12 animate-spin text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <h2 className="mb-2 text-2xl font-semibold text-gray-900">
          Authenticating...
        </h2>
        <p className="text-gray-600">Please wait while we log you in.</p>
      </div>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="mb-2 text-2xl font-semibold text-gray-900">
            Loading...
          </h2>
        </div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
