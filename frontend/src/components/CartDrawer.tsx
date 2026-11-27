"use client";

import React from "react";
import { ShoppingBag, X, ArrowRight } from "lucide-react";
import { CartData } from "@/types/chat";

interface CartDrawerProps {
  isOpen: boolean;
  cart: CartData;
  onClose: () => void;
  onCheckout: () => void;
}

export function CartDrawer({ isOpen, cart, onClose, onCheckout }: CartDrawerProps) {
  if (!isOpen) return null;

  const formattedSubtotal = `₹${Number(cart.total_price || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
  })}`;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-fadeIn"
      />

      {/* Slide Drawer */}
      <aside className="fixed top-0 right-0 bottom-0 w-[420px] max-w-[90vw] bg-gray-900 border-l border-white/10 z-50 flex flex-col shadow-2xl animate-slideLeft">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5 font-bold text-base text-white">
            <ShoppingBag className="w-5 h-5 text-indigo-400" />
            <span>Your Shopping Cart ({cart.total_items})</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {cart.items.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="text-4xl mb-3">🛍️</div>
              <h5 className="font-bold text-white text-sm mb-1">Your cart is empty</h5>
              <p className="text-xs text-gray-400 max-w-[240px] mx-auto">
                Ask Nova to search for products and add them directly to your order!
              </p>
            </div>
          ) : (
            cart.items.map((item) => (
              <div
                key={item.id}
                className="bg-gray-800/80 border border-white/5 rounded-xl p-3.5 flex items-center justify-between gap-3"
              >
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-white line-clamp-1">{item.name}</span>
                  <span className="text-[11px] text-gray-400">
                    Qty: {item.quantity} × ₹{Number(item.unit_price).toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="text-xs font-bold text-emerald-400 whitespace-nowrap">
                  ₹{Number(item.subtotal).toLocaleString("en-IN")}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-white/10 bg-gray-900/90 space-y-3">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Subtotal</span>
            <span className="font-semibold text-white">{formattedSubtotal}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Standard Delivery</span>
            <span className="text-emerald-400 font-bold uppercase tracking-wider text-[11px]">
              FREE
            </span>
          </div>
          <div className="h-px bg-white/10 my-2" />
          <div className="flex justify-between items-baseline text-sm font-bold text-white">
            <span>Order Total</span>
            <span className="text-xl font-extrabold text-indigo-400">{formattedSubtotal}</span>
          </div>

          <button
            onClick={() => {
              onClose();
              onCheckout();
            }}
            disabled={cart.total_items === 0}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 transition"
          >
            <span>Proceed to Checkout with Nova</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </>
  );
}
