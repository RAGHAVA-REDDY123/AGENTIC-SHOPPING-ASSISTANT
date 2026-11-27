"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface WelcomeHeroProps {
  onSelectPrompt: (query: string) => void;
}

const POPULAR_PROMPTS = [
  {
    icon: "💻",
    title: "Gaming Laptops",
    desc: "Under ₹1.5L with 16GB RAM",
    query: "Suggest best gaming laptops under 1.5 lakh with 16GB RAM",
  },
  {
    icon: "⚖️",
    title: "Product Comparison",
    desc: "MacBook Pro M3 vs Dell XPS 15",
    query: "Compare Apple MacBook Pro 14 M3 vs Dell XPS 15",
  },
  {
    icon: "📱",
    title: "Flagship Smartphones",
    desc: "Best camera reviews & specs",
    query: "Show me flagship smartphones with best camera reviews",
  },
  {
    icon: "🎧",
    title: "Wireless Audio",
    desc: "ANC headphones with great mics",
    query: "Show me noise cancelling wireless headphones with long battery",
  },
];

export function WelcomeHero({ onSelectPrompt }: WelcomeHeroProps) {
  return (
    <div className="text-center py-12 px-4 max-w-2xl mx-auto flex flex-col items-center animate-fadeIn">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center mb-5 shadow-lg shadow-indigo-500/10">
        <Sparkles className="w-8 h-8 text-indigo-400" />
      </div>

      <h1 className="text-3xl font-extrabold tracking-tight mb-2.5 bg-gradient-to-r from-white via-indigo-100 to-indigo-300 bg-clip-text text-transparent">
        Welcome to ShopPilot AI
      </h1>
      <p className="text-sm text-gray-300 leading-relaxed mb-8 max-w-lg">
        Your personal shopping helper. Tell me what you're looking for, and I'll help you find, compare, and order the best products easily.
      </p>

      <div className="w-full">
        <div className="text-[11px] font-bold text-gray-500 tracking-wider mb-3 uppercase">
          Popular Shopping Inquiries
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          {POPULAR_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPrompt(p.query)}
              className="flex items-center gap-3.5 p-3.5 rounded-xl bg-gray-900 border border-white/10 hover:border-indigo-500/40 hover:bg-gray-800/80 transition-all duration-200 group shadow-sm hover:shadow-md"
            >
              <span className="text-2xl">{p.icon}</span>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-white group-hover:text-indigo-300 transition">
                  {p.title}
                </span>
                <span className="text-[11px] text-gray-400">{p.desc}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
