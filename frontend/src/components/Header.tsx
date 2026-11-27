"use client";

import React from "react";
import { ShoppingBag } from "lucide-react";
import { ConnectionStatus, CartData } from "@/types/chat";

interface HeaderProps {
  status?: ConnectionStatus;
  cart: CartData;
  onOpenCart: () => void;
  onOpenCatalog?: () => void;
  onClearChat?: () => void;
}

export function Header({ cart, onOpenCart }: HeaderProps) {
  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-white/10 bg-gray-900/80 backdrop-blur-md sticky top-0 z-20">
      {/* Brand Identity - ShopPilot AI (Enlarged) */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
          <ShoppingBag className="w-5 h-5 text-white" />
        </div>
        <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
          ShopPilot <span className="text-indigo-400">AI</span>
        </h1>
      </div>

      {/* Action Controls - Only Cart Button */}
      <div className="flex items-center">
        <button
          onClick={onOpenCart}
          className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-xs font-semibold text-white transition shadow-sm active:scale-95"
        >
          <ShoppingBag className="w-4 h-4 text-indigo-400" />
          <span className="font-bold">Cart</span>
          <span className="px-2 py-0.5 rounded-full bg-indigo-600 text-[11px] font-bold text-white min-w-5 text-center">
            {cart.total_items}
          </span>
          {cart.total_price > 0 && (
            <span className="hidden sm:inline font-bold text-indigo-200">
              ₹{cart.total_price.toLocaleString("en-IN")}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
