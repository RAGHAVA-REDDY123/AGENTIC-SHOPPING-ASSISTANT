"use client";

import React, { useRef, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { WelcomeHero } from "@/components/WelcomeHero";
import { MessageItem } from "@/components/MessageItem";
import { Composer } from "@/components/Composer";
import { CartDrawer } from "@/components/CartDrawer";
import { CatalogDrawer } from "@/components/CatalogDrawer";
import { useShoppingWebSocket } from "@/hooks/useShoppingWebSocket";
import { Loader2, CheckCircle2, AlertTriangle } from "lucide-react";

export default function Home() {
  const {
    status,
    messages,
    cart,
    liveActivity,
    isGenerating,
    toast,
    sendMessage,
    addToCart,
    clearChat,
    stopGeneration,
  } = useShoppingWebSocket();

  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);

  const viewportRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on streaming
  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
    }
  }, [messages, liveActivity]);

  return (
    <div className="flex flex-col h-screen w-full bg-[#0B0F19] text-gray-100 overflow-hidden relative">
      {/* Top Header */}
      <Header
        status={status}
        cart={cart}
        onOpenCart={() => setIsCartOpen(true)}
        onOpenCatalog={() => setIsCatalogOpen(true)}
        onClearChat={clearChat}
      />

      {/* Main Chat Scroll Viewport */}
      <main ref={viewportRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 scroll-smooth">
        <div className="max-w-3xl mx-auto flex flex-col gap-6 min-h-full">
          {messages.length === 0 ? (
            <WelcomeHero onSelectPrompt={sendMessage} />
          ) : (
            messages.map((m) => (
              <MessageItem
                key={m.id}
                message={m}
                onAddToCart={addToCart}
                onSendQuery={sendMessage}
              />
            ))
          )}

          {/* Live Activity Ticker */}
          {liveActivity && (
            <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/25 text-xs text-indigo-300 w-fit mx-auto animate-fadeIn">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>{liveActivity}</span>
            </div>
          )}
        </div>
      </main>

      {/* Composer Input Bar */}
      <Composer
        isGenerating={isGenerating}
        onSendMessage={sendMessage}
        onStopGeneration={stopGeneration}
      />

      {/* Slide-over Drawers */}
      <CartDrawer
        isOpen={isCartOpen}
        cart={cart}
        onClose={() => setIsCartOpen(false)}
        onCheckout={() => sendMessage("I would like to proceed with checkout for the items in my cart.")}
      />

      <CatalogDrawer
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
        onSelectProduct={sendMessage}
      />

      {/* Floating Toast Notification */}
      {toast && (
        <div className="fixed bottom-20 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-gray-800 border border-white/10 text-xs font-semibold text-white shadow-2xl animate-fadeIn">
          {toast.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}
