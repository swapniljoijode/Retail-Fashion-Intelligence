"use client";

import Image from "next/image";
import type { CategoryImage } from "@/lib/types";

interface CategoryImageCardProps {
  category: string;
  image:    CategoryImage | undefined;
  revenue:  string;
  margin:   string;
  units:    string;
}

const CATEGORY_ICONS: Record<string, string> = {
  Tops:        "👕",
  Bottoms:     "👖",
  Dresses:     "👗",
  Outerwear:   "🧥",
  Footwear:    "👟",
  Accessories: "👜",
};

export default function CategoryImageCard({
  category,
  image,
  revenue,
  margin,
  units,
}: CategoryImageCardProps) {
  return (
    <div
      className="flex flex-col rounded-xl overflow-hidden"
      style={{ background: "var(--surface-2)", border: "1px solid var(--border)" }}
    >
      {/* Thumbnail */}
      <div className="relative w-full" style={{ aspectRatio: "1 / 1" }}>
        {image ? (
          <Image
            src={image.url}
            alt={image.alt}
            fill
            sizes="(max-width: 768px) 50vw, 200px"
            className="object-cover"
            unoptimized
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-4xl"
            style={{ background: "var(--surface)", color: "var(--muted)" }}
          >
            {CATEGORY_ICONS[category] ?? "🏷️"}
          </div>
        )}
        {/* Category label overlay */}
        <div
          className="absolute bottom-0 left-0 right-0 px-2 py-1 text-xs font-semibold truncate"
          style={{
            background: "linear-gradient(to top, rgba(7,7,14,0.85), transparent)",
            color: "var(--brand-gold)",
          }}
        >
          {category}
        </div>
      </div>

      {/* Metrics */}
      <div className="px-3 py-2 space-y-0.5">
        <p className="text-xs font-mono" style={{ color: "var(--brand-gold)" }}>{revenue}</p>
        <div className="flex justify-between text-xs font-mono" style={{ color: "var(--muted)" }}>
          <span>{margin} margin</span>
          <span>{units} units</span>
        </div>
      </div>

      {/* Image credit */}
      {image && image.photographer !== "Unsplash" && (
        <p className="px-3 pb-2 truncate" style={{ color: "var(--muted)", fontSize: 10 }}>
          📷 {image.photographer}
        </p>
      )}
    </div>
  );
}
