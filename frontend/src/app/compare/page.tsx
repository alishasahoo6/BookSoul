"use client";

import { Scale, Plus } from "lucide-react";

export default function ComparePage() {
  const dimensions = [
    { label: "Pacing (Slow Burn vs Kinetic)" },
    { label: "Emotional Depth" },
    { label: "Comfort Level" },
    { label: "Angst & Tension" },
    { label: "Humor & Wit" },
    { label: "World Building Complexity" },
  ];

  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Book Comparison Engine</h1>
        <p className="text-xs text-muted-foreground">Contrast the narrative structure and DNA profiles of two titles</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Book Slot */}
        <div className="border border-dashed border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center gap-4 bg-white/[0.005] hover:bg-white/[0.01] transition-colors duration-300 cursor-pointer">
          <div className="p-4 rounded-full bg-white/[0.02] border border-white/[0.05]">
            <Plus className="w-6 h-6 text-muted-foreground" />
          </div>
          <span className="text-xs font-semibold text-muted-foreground/80">Select Primary Book</span>
        </div>

        {/* Right Book Slot */}
        <div className="border border-dashed border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center gap-4 bg-white/[0.005] hover:bg-white/[0.01] transition-colors duration-300 cursor-pointer">
          <div className="p-4 rounded-full bg-white/[0.02] border border-white/[0.05]">
            <Plus className="w-6 h-6 text-muted-foreground" />
          </div>
          <span className="text-xs font-semibold text-muted-foreground/80">Select Comparison Book</span>
        </div>
      </div>

      {/* Comparison dimensions mockup */}
      <div className="glass-panel p-6 rounded-2xl bg-white/[0.01] flex flex-col gap-6 mt-4">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Scale className="w-4 h-4 text-accent-gold" /> Comparison Matrix
        </h4>

        <div className="flex flex-col gap-5">
          {dimensions.map((dim, idx) => (
            <div key={idx} className="flex flex-col gap-2">
              <span className="text-xs text-muted-foreground">{dim.label}</span>
              <div className="grid grid-cols-3 items-center gap-4">
                {/* Book 1 Bar (mock) */}
                <div className="h-2 rounded-full bg-white/[0.03] overflow-hidden flex justify-end">
                  <div className="w-1/2 h-full bg-accent-purple/35 rounded-full" />
                </div>
                
                {/* Center label divider */}
                <div className="text-center text-[10px] text-muted-foreground/50 font-bold uppercase tracking-widest">
                  VS
                </div>

                {/* Book 2 Bar (mock) */}
                <div className="h-2 rounded-full bg-white/[0.03] overflow-hidden">
                  <div className="w-3/4 h-full bg-accent-pink/35 rounded-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
