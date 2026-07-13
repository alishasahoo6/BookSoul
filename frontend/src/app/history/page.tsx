"use client";

import { useEffect, useState } from "react";
import { Calendar, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HistoryPage() {
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem("booksoul_history");
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch (e) {
        console.error(e);
      }
    } else {
      // Seed some default history items
      const defaults = [
        "Matched recommendation 'The Starless Sea' (98% match)",
        "Compared 'The Hobbit' vs 'The Name of the Wind'",
        "Logged new mood: 'Cozy fantasy vibes'",
        "Added 'A Court of Thorns and Roses' to shelf"
      ];
      setHistory(defaults);
      localStorage.setItem("booksoul_history", JSON.stringify(defaults));
    }
  }, []);

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("booksoul_history");
  };

  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-heading font-bold text-gradient-gold">Discovery History</h1>
          <p className="text-xs text-muted-foreground">A timeline of your search requests, comparisons, and matching actions</p>
        </div>
        {history.length > 0 && (
          <Button 
            onClick={clearHistory}
            variant="destructive"
            className="rounded-full px-4 py-2 text-xs font-semibold cursor-pointer flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" /> Clear History
          </Button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="border border-dashed border-white/10 rounded-2xl p-16 text-center flex flex-col items-center justify-center gap-3 bg-white/[0.005]">
          <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05] mb-2">
            <Calendar className="w-5 h-5 text-muted-foreground/60" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">Timeline is Empty</h4>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            Your search history and match evaluations will be recorded here automatically.
          </p>
        </div>
      ) : (
        /* Timeline Layout */
        <div className="relative border-l border-white/[0.08] ml-4 pl-6 flex flex-col gap-6 mt-4">
          {history.map((action, idx) => (
            <div key={idx} className="relative group">
              {/* Dot indicator */}
              <div className="absolute -left-[31px] top-1.5 w-2.5 h-2.5 rounded-full bg-white/[0.2] border-2 border-background group-hover:bg-accent-purple group-hover:scale-110 transition-all duration-300" />
              
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-muted-foreground/60 font-semibold font-sans">
                  {idx === 0 ? "Today" : idx === 1 ? "Yesterday" : `July ${12 - idx}, 2026`}
                </span>
                <p className="text-xs text-foreground/80 leading-relaxed font-sans">
                  {action}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
