"use client";

import React, { useEffect, useState } from "react";
import { Layers, X, Star } from "lucide-react";
import { ProductItem } from "@/types/chat";

interface CatalogDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectProduct: (name: string) => void;
}

export function CatalogDrawer({ isOpen, onClose, onSelectProduct }: CatalogDrawerProps) {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && products.length === 0) {
      setLoading(true);
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      fetch(`${apiBase}/api/products/featured?limit=12`)
        .then((res) => res.json())
        .then((data) => {
          setProducts(data.products || []);
        })
        .catch((err) => console.error("Error fetching catalog:", err))
        .finally(() => setLoading(false));
    }
  }, [isOpen, products.length]);

  if (!isOpen) return null;

  return (
    <>
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-fadeIn"
      />
      <aside className="fixed top-0 right-0 bottom-0 w-[420px] max-w-[90vw] bg-gray-900 border-l border-white/10 z-50 flex flex-col shadow-2xl animate-slideLeft">
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5 font-bold text-base text-white">
            <Layers className="w-5 h-5 text-indigo-400" />
            <span>Store Catalog Showcase</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {loading ? (
            <div className="text-center py-16 text-gray-400 text-xs">Loading catalog items...</div>
          ) : products.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-xs">No products found.</div>
          ) : (
            products.map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  onClose();
                  onSelectProduct(`Tell me details and reviews for ${p.name}`);
                }}
                className="bg-gray-800/80 hover:bg-gray-800 border border-white/5 hover:border-indigo-500/40 rounded-xl p-3.5 flex items-center justify-between gap-3 cursor-pointer transition"
              >
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-white line-clamp-1">{p.name}</span>
                  <div className="flex items-center gap-2 text-[11px] text-gray-400">
                    <span>{p.brand || "Brand"}</span>
                    <span>•</span>
                    <span className="flex items-center gap-0.5 text-amber-400">
                      <Star className="w-3 h-3 fill-amber-400" />
                      {Number(p.rating || 4.5).toFixed(1)}
                    </span>
                  </div>
                </div>
                <div className="text-xs font-bold text-white whitespace-nowrap">
                  ₹{Number(p.price).toLocaleString("en-IN")}
                </div>
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  );
}
