"use client";

import React from "react";
import { Star, ShoppingCart, FileText } from "lucide-react";
import { ProductItem } from "@/types/chat";

interface ProductCardProps {
  product: ProductItem;
  onAddToCart: (id: number) => void;
  onViewSpecs: (name: string) => void;
}

export function ProductCard({ product, onAddToCart, onViewSpecs }: ProductCardProps) {
  const formattedPrice = `₹${Number(product.price).toLocaleString("en-IN")}`;
  const origPrice =
    product.original_price && product.original_price > product.price
      ? `₹${Number(product.original_price).toLocaleString("en-IN")}`
      : null;

  return (
    <div className="bg-[#161F30] border border-white/10 hover:border-indigo-500/40 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 hover:-translate-y-1 shadow-md hover:shadow-indigo-500/10 group">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white/5 text-gray-400">
            {product.category_slug || "Product"}
          </span>
          <span
            className={`text-[11px] font-semibold flex items-center gap-1 ${
              product.in_stock ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            ● {product.in_stock ? "In Stock" : "Out of Stock"}
          </span>
        </div>

        {/* Product Title & Brand */}
        <h4 className="text-sm font-bold text-white leading-snug line-clamp-2 mb-1 group-hover:text-indigo-200 transition">
          {product.name}
        </h4>
        <p className="text-xs text-gray-400 mb-2">{product.brand || ""}</p>

        {/* Rating */}
        <div className="flex items-center gap-1.5 text-xs text-amber-400 mb-3">
          <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
          <span className="font-bold">{Number(product.rating || 4.5).toFixed(1)}</span>
          <span className="text-gray-500 text-[11px]">
            ({Number(product.review_count || 120).toLocaleString()} reviews)
          </span>
        </div>
      </div>

      {/* Pricing & CTA Buttons */}
      <div>
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-lg font-extrabold text-white">{formattedPrice}</span>
          {origPrice && <span className="text-xs text-gray-500 line-through">{origPrice}</span>}
          {product.discount_percent && product.discount_percent > 0 ? (
            <span className="text-[11px] font-bold text-emerald-400">
              {product.discount_percent}% OFF
            </span>
          ) : null}
        </div>

        <div className="grid grid-cols-[1fr_auto] gap-2">
          <button
            onClick={() => onAddToCart(product.id)}
            disabled={!product.in_stock}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold transition shadow-sm"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            <span>Add to Cart</span>
          </button>

          <button
            onClick={() => onViewSpecs(product.name)}
            className="flex items-center justify-center px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white text-xs font-semibold transition"
          >
            <FileText className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
