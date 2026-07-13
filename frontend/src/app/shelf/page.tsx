"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Library } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ShelfPage() {
  const shelfTabs = ["All Collection", "To Read", "Currently Reading", "Completed"];
  const [activeSubTab, setActiveSubTab] = useState("All Collection");

  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-heading font-bold text-gradient-gold">My Personal Shelf</h1>
          <p className="text-xs text-muted-foreground">Keep track of your current read queue and favorite discoveries</p>
        </div>
        <Button className="bg-white/[0.04] hover:bg-white/[0.08] text-foreground border border-white/10 rounded-full px-5 py-4 text-xs font-semibold cursor-pointer">
          Create Custom Shelf +
        </Button>
      </div>

      {/* Shelf filter tabs */}
      <div className="flex border-b border-white/[0.05] gap-6 text-sm font-medium">
        {shelfTabs.map((tab) => (
          <span 
            key={tab} 
            onClick={() => setActiveSubTab(tab)}
            className={`pb-3 cursor-pointer transition-all duration-300 relative ${
              activeSubTab === tab
                ? "text-accent-purple font-semibold" 
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
            {activeSubTab === tab && (
              <motion.div layoutId="shelfActiveLine" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-purple" />
            )}
          </span>
        ))}
      </div>

      {/* Shelf grid skeleton items */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-5">
        {Array.from({ length: 6 }).map((_, idx) => (
          <div key={idx} className="flex flex-col gap-2.5 bg-white/[0.005] hover:bg-white/[0.01] transition-all p-3 rounded-xl border border-white/[0.04] cursor-pointer">
            <div className="aspect-[2/3] rounded-lg bg-white/[0.02] border border-white/[0.05] animate-pulse flex items-center justify-center">
              <Library className="w-6 h-6 text-white/[0.02]" />
            </div>
            <div className="h-3.5 w-4/5 rounded bg-white/[0.06] animate-pulse mt-1" />
            <div className="h-3 w-1/2 rounded bg-white/[0.03] animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
