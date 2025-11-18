"use client";

import React from "react";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth";
import { Button } from "../ui/button";
import { Plus, User } from "phosphor-react";

export function TopBar() {
  const { user, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="flex items-center gap-4">
        <Link href="/" className="text-xl font-bold">
          Muset
        </Link>
        <Button variant="ghost" size="sm">
          <Plus size={20} weight="bold" />
          New Page
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-sm text-gray-600">
          AI chats left: <span className="font-semibold">35</span>
        </div>
        <Button variant="outline" size="sm">
          Upgrade
        </Button>

        <div className="relative">
          <button className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 hover:bg-gray-300">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.name}
                className="h-full w-full rounded-full object-cover"
              />
            ) : (
              <User size={20} />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
