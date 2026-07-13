"use client";

import { useEffect, useState } from "react";
import { Star, Library } from "lucide-react";

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    // Read local favorites from localStorage (if any)
    const stored = localStorage.getItem("booksoul_favorites");
    if (stored) {
      try {
        setFavorites(JSON.parse(stored));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Favorite Literature</h1>
        <p className="text-xs text-muted-foreground">A curated shelf of your absolute favorite books</p>
      </div>

      {favorites.length === 0 ? (
        <div className="border border-dashed border-white/10 rounded-2xl p-16 text-center flex flex-col items-center justify-center gap-3 bg-white/[0.005]">
          <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05] mb-2">
            <Star className="w-5 h-5 text-muted-foreground/60" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">No Favorites Added Yet</h4>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            Click the heart icon on any recommendation match to add a book to your favorites collection.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-6">
          {favorites.map((title) => (
            <div key={title} className="glass-panel p-4 rounded-2xl flex flex-col gap-3 relative bg-white/[0.01]">
              <Star className="w-4 h-4 text-accent-gold fill-accent-gold absolute top-4 right-4 z-10" />
              
              <div className="aspect-[2/3] w-full rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center justify-center">
                <Library className="w-10 h-10 text-white/[0.03]" />
              </div>
              
              <div className="flex flex-col gap-1">
                <h4 className="text-sm font-heading font-bold text-foreground line-clamp-2">{title}</h4>
                <span className="text-[10px] text-muted-foreground">Saved to favorites</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
