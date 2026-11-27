"use client";

import React, { useRef, useState } from "react";
import { Send, Square } from "lucide-react";

interface ComposerProps {
  isGenerating: boolean;
  onSendMessage: (text: string) => void;
  onStopGeneration: () => void;
}

export function Composer({ isGenerating, onSendMessage, onStopGeneration }: ComposerProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || isGenerating) return;
    onSendMessage(input);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const target = e.target;
    target.style.height = "auto";
    target.style.height = `${Math.min(target.scrollHeight, 140)}px`;
  };

  return (
    <footer className="px-5 pb-5 pt-1 bg-gradient-to-t from-gray-950 via-gray-950/80 to-transparent sticky bottom-0 z-10">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        <div className="bg-gray-800/90 border border-white/10 focus-within:border-indigo-500/50 rounded-2xl p-2.5 px-4 flex items-end gap-3 shadow-xl transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask Nova (e.g. 'Show me 4K monitors under 50k', 'Add product 1 to cart', 'Checkout')..."
            className="flex-1 bg-transparent border-none outline-none text-white text-[14.5px] leading-relaxed resize-none max-h-36 min-h-[26px] py-1 placeholder:text-gray-500 font-sans"
          />

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {isGenerating ? (
              <button
                onClick={onStopGeneration}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-bold transition"
              >
                <Square className="w-3.5 h-3.5 fill-rose-400" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-9 h-9 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed text-white flex items-center justify-center transition shadow-md shadow-indigo-500/20"
              >
                <Send className="w-4 h-4 ml-0.5" />
              </button>
            )}
          </div>
        </div>

        <div className="flex justify-center items-center text-[11px] text-gray-500 px-2">
          <span>
            Press <strong className="text-gray-400">Enter</strong> to send, <strong className="text-gray-400">Shift+Enter</strong> for newline
          </span>
        </div>
      </div>
    </footer>
  );
}
