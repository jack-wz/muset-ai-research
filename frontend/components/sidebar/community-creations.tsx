"use client";

import React from "react";
import { Card } from "../ui/card";
import { CaretDown, ArrowRight } from "phosphor-react";

const SAMPLE_CREATIONS = [
  {
    id: "1",
    title: "The Future of AI Writing",
    type: "Article",
    author: "Sarah Chen",
    coverUrl: null,
  },
  {
    id: "2",
    title: "Creating Engaging Content",
    type: "Guide",
    author: "Mike Johnson",
    coverUrl: null,
  },
];

export function CommunityCreations() {
  const [isExpanded, setIsExpanded] = React.useState(true);

  return (
    <div className="flex-1 border-t border-gray-200 p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mb-4 flex w-full items-center justify-between text-left"
      >
        <h2 className="text-lg font-semibold">Community Creations</h2>
        <CaretDown
          size={20}
          className={`transition-transform ${isExpanded ? "" : "-rotate-90"}`}
        />
      </button>

      {isExpanded && (
        <>
          <div className="space-y-3">
            {SAMPLE_CREATIONS.map((creation) => (
              <Card
                key={creation.id}
                className="cursor-pointer overflow-hidden transition-shadow hover:shadow-md"
              >
                <div className="aspect-video bg-gradient-to-br from-blue-400 to-purple-500" />
                <div className="p-3">
                  <div className="mb-1 text-xs text-gray-500">{creation.type}</div>
                  <h4 className="mb-2 font-medium">{creation.title}</h4>
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full bg-gray-300" />
                    <span className="text-xs text-gray-600">{creation.author}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 py-2 text-sm hover:bg-gray-50">
            Explore Community Creations
            <ArrowRight size={16} />
          </button>
        </>
      )}
    </div>
  );
}
