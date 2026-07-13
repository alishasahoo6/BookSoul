"use client";

import { Heart, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function MoodPage() {
  const recentLogs = [
    { date: "July 12, 2026", text: "Looking for an immersive escapist fantasy with beautiful prose, slow build romance, and high magic. No urban settings.", vibe: "Cozy & Immersive" },
    { date: "July 08, 2026", text: "Need something extremely fast-paced and gripping. A sci-fi space opera or thriller that keeps me up all night.", vibe: "High-Stakes Intense" },
  ];

  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Mood Journal</h1>
        <p className="text-xs text-muted-foreground">Log your thoughts and emotions; the system infers recommendations directly from your words</p>
      </div>

      <div className="glass-panel p-6 rounded-2xl bg-white/[0.01] flex flex-col gap-4">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Heart className="w-4 h-4 text-accent-pink" /> How are you feeling today?
        </h4>
        <textarea
          disabled
          placeholder="Describe your current state, desired setting, pacing, or literary cravings. E.g. 'I want a rainy day mystery set in a small coastal town, very atmospheric, slow paced, with a lonely protagonist...'"
          className="w-full h-36 bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 text-xs text-muted-foreground resize-none cursor-not-allowed outline-none"
        />
        <div className="flex justify-between items-center mt-1">
          <span className="text-[10px] text-muted-foreground/60 italic font-sans">
            AI analysis engine will extract DNA dimensions automatically
          </span>
          <Button disabled className="bg-gradient-purple-pink text-white rounded-full px-5 py-4 text-xs font-semibold cursor-not-allowed opacity-50">
            Submit Mood Log
          </Button>
        </div>
      </div>

      {/* History logs list */}
      <div className="flex flex-col gap-4 mt-2">
        <h4 className="text-xs font-bold text-muted-foreground/60 tracking-wider uppercase font-sans">Past Mood Logs</h4>
        
        <div className="flex flex-col gap-3">
          {recentLogs.map((log, idx) => (
            <div key={idx} className="glass-panel p-4 rounded-xl bg-white/[0.005] hover:bg-white/[0.01] transition-all flex flex-col sm:flex-row justify-between items-start gap-4 border-white/[0.04]">
              <div className="flex flex-col gap-1.5 flex-1">
                <span className="text-[10px] text-muted-foreground/50 font-semibold flex items-center gap-1 font-sans">
                  <Calendar className="w-3 h-3" /> {log.date}
                </span>
                <p className="text-xs text-muted-foreground/90 leading-relaxed font-sans font-light">
                  &ldquo;{log.text}&rdquo;
                </p>
              </div>
              <span className="text-[10px] bg-accent-purple/10 border border-accent-purple/20 text-accent-purple px-2.5 py-1 rounded-full font-medium shrink-0 font-sans">
                Inferred: {log.vibe}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
