"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth";

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuthStore();
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError("Authentication failed. Please try again.");
      setTimeout(() => router.push("/login"), 3000);
      return;
    }

    if (code) {
      handleOAuthCallback(code);
    } else {
      setError("No authorization code received.");
      setTimeout(() => router.push("/login"), 3000);
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string) => {
    try {
      // Exchange code for token
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/google/callback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to authenticate");
      }

      const data = await response.json();
      login(data.user, data.token);
      router.push("/workspace");
    } catch (err) {
      setError("Authentication failed. Please try again.");
      setTimeout(() => router.push("/login"), 3000);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        {error ? (
          <>
            <div className="mb-4 text-4xl">❌</div>
            <h1 className="mb-2 text-2xl font-bold text-gray-900">{error}</h1>
            <p className="text-gray-600">Redirecting to login...</p>
          </>
        ) : (
          <>
            <div className="mb-4">
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
            <h1 className="mb-2 text-2xl font-bold text-gray-900">Authenticating...</h1>
            <p className="text-gray-600">Please wait while we sign you in.</p>
          </>
        )}
      </div>
    </div>
  );
}
