"use client";

import React from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Lightbulb, ArrowRight, Sparkle } from "phosphor-react";

interface PromptSuggestion {
  id: string;
  category: "question" | "topic" | "angle";
  text: string;
  icon: string;
}

interface PromptSuggestionsProps {
  onSelectPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS: PromptSuggestion[] = [
  {
    id: "1",
    category: "topic",
    text: "Remix 'AI career transitions' for Twitter, Medium, and YouTube.",
    icon: "📝",
  },
  {
    id: "2",
    category: "topic",
    text: "Give me 5 viral lifestyle blog topics for this week.",
    icon: "💡",
  },
  {
    id: "3",
    category: "question",
    text: "Gold investment: Yes or no? Analyze with expert trends",
    icon: "💰",
  },
  {
    id: "4",
    category: "angle",
    text: "Write a thought-provoking opening for a tech article",
    icon: "🚀",
  },
  {
    id: "5",
    category: "question",
    text: "What are the top 3 challenges in remote work?",
    icon: "🏠",
  },
  {
    id: "6",
    category: "topic",
    text: "Create a compelling story about sustainable living",
    icon: "🌱",
  },
];

export function PromptSuggestions({ onSelectPrompt }: PromptSuggestionsProps) {
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);

  const categories = [
    { id: "question", label: "Questions", icon: "❓" },
    { id: "topic", label: "Topics", icon: "📚" },
    { id: "angle", label: "Angles", icon: "🎯" },
  ];

  const filteredPrompts = selectedCategory
    ? SAMPLE_PROMPTS.filter((p) => p.category === selectedCategory)
    : SAMPLE_PROMPTS;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="mb-4 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-yellow-400 to-orange-500">
            <Sparkle size={32} weight="fill" className="text-white" />
          </div>
        </div>
        <h2 className="mb-2 text-2xl font-bold">Get Inspired</h2>
        <p className="text-gray-600">
          Start with a prompt or let AI suggest ideas based on your interests
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex justify-center gap-2">
        <Button
          variant={selectedCategory === null ? "primary" : "ghost"}
          size="sm"
          onClick={() => setSelectedCategory(null)}
        >
          All
        </Button>
        {categories.map((cat) => (
          <Button
            key={cat.id}
            variant={selectedCategory === cat.id ? "primary" : "ghost"}
            size="sm"
            onClick={() => setSelectedCategory(cat.id)}
          >
            <span className="mr-1">{cat.icon}</span>
            {cat.label}
          </Button>
        ))}
      </div>

      {/* Prompt Cards */}
      <div className="grid gap-3 md:grid-cols-2">
        {filteredPrompts.map((prompt) => (
          <Card
            key={prompt.id}
            className="cursor-pointer p-4 transition-shadow hover:shadow-lg"
            onClick={() => onSelectPrompt(prompt.text)}
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl">{prompt.icon}</div>
              <div className="flex-1">
                <p className="text-sm font-medium">{prompt.text}</p>
              </div>
              <ArrowRight size={20} className="text-gray-400" />
            </div>
          </Card>
        ))}
      </div>

      {/* Generate More */}
      <div className="text-center">
        <Button variant="outline">
          <Lightbulb size={20} weight="fill" />
          Generate More Ideas
        </Button>
      </div>
    </div>
  );
}
