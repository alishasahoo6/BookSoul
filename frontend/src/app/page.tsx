"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  BookOpen, 
  Scale, 
  Library, 
  Heart, 
  Star, 
  Compass,
  ArrowRight,
  TrendingUp,
  BarChart3,
  Calendar,
  ChevronRight,
  Plus
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Fade/slide motion animation variants
const tabTransition = {
  initial: { opacity: 0, y: 15 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -15 },
  transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] }
};

function DashboardContent() {
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") || "Home";

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={activeTab}
        initial="initial"
        animate="animate"
        exit="exit"
        variants={tabTransition}
        className="w-full"
      >
        {activeTab === "Home" && <HomeView />}
        {activeTab === "Recommendations" && <RecommendationsView />}
        {activeTab === "Compare" && <CompareView />}
        {activeTab === "Shelf" && <ShelfView />}
        {activeTab === "Mood" && <MoodView />}
        {activeTab === "Favorites" && <FavoritesView />}
        {activeTab === "History" && <HistoryView />}
      </motion.div>
    </AnimatePresence>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col items-center justify-center p-12 min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="text-3xl animate-bounce">🔮</div>
          <span className="text-sm text-muted-foreground animate-pulse font-medium">Opening BookSoul...</span>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}

// ==========================================
// 1. HOME TAB VIEW
// ==========================================
function HomeView() {
  const popularMoods = [
    { label: "Pulse-Pounding & Wild", emoji: "⚡" },
    { label: "Atmospheric & Dread-Soaked", emoji: "🕯️" },
    { label: "Cozy Romance", emoji: "☕" },
    { label: "Mind-Bending & Tense", emoji: "🌀" },
    { label: "Intimate & Raw", emoji: "🍷" },
    { label: "Fast-Paced & Gripping", emoji: "🚀" },
    { label: "Magical & Immersive", emoji: "🔮" },
    { label: "Deeply Introspective", emoji: "🌲" },
  ];

  return (
    <div className="flex flex-col gap-10">
      {/* Hero Section */}
      <section className="relative rounded-3xl overflow-hidden glass-panel p-8 md:p-12 shadow-[0_20px_50px_rgba(0,0,0,0.3)] border-gradient-glow">
        {/* Soft background gradient glows */}
        <div className="absolute top-0 left-0 -translate-x-1/4 -translate-y-1/4 w-96 h-96 bg-accent-purple/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-0 right-0 translate-x-1/4 translate-y-1/4 w-96 h-96 bg-accent-pink/10 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="max-w-2xl relative z-10 flex flex-col items-start gap-4">
          <div className="inline-flex items-center gap-1.5 bg-accent-gold/10 border border-accent-gold/20 px-3 py-1 rounded-full text-xs font-semibold text-accent-gold tracking-wide">
            <Sparkles className="w-3 h-3 animate-pulse" /> Introducing BookSoul DNA
          </div>
          <h1 className="text-4xl md:text-5xl font-heading font-bold text-gradient-gold leading-tight tracking-tight mt-2">
            Discover books that <br />
            truly understand you.
          </h1>
          <p className="text-sm md:text-base text-muted-foreground/90 leading-relaxed font-sans font-light mt-2 max-w-xl">
            BookSoul shifts literary discovery from simple queries to deep semantic matching. 
            Describe your mood, select your favorite genres, and explore literature tailored to 
            your exact emotional DNA, pacing style, and character tropes.
          </p>
          <div className="flex flex-wrap gap-4 mt-4">
            <Button className="bg-gradient-purple-pink hover:opacity-90 rounded-full px-6 py-5 text-sm font-semibold transition-all duration-300 flex items-center gap-2 cursor-pointer shadow-[0_4px_20px_rgba(167,139,250,0.25)]">
              Begin Exploration <ArrowRight className="w-4 h-4" />
            </Button>
            <Button variant="outline" className="border-white/10 bg-white/[0.02] hover:bg-white/[0.06] rounded-full px-6 py-5 text-sm font-semibold cursor-pointer">
              View Your Shelf
            </Button>
          </div>
        </div>
      </section>

      {/* Popular Moods */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <h3 className="text-lg font-heading font-semibold text-foreground">What&apos;s your current vibe?</h3>
            <p className="text-xs text-muted-foreground">Select a literary mood or pacing to populate recommendations</p>
          </div>
          <span className="text-xs text-accent-purple hover:underline cursor-pointer font-medium flex items-center gap-1">
            See all moods <ChevronRight className="w-3 h-3" />
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mt-1">
          {popularMoods.map((mood, idx) => (
            <motion.div
              whileHover={{ y: -3, borderColor: "rgba(167, 139, 250, 0.3)" }}
              key={idx}
              className="glass-panel p-4 rounded-xl flex flex-col items-center justify-center gap-3 text-center cursor-pointer select-none transition-all duration-300 hover:bg-white/[0.02]"
            >
              <span className="text-2xl">{mood.emoji}</span>
              <span className="text-[11px] font-medium text-muted-foreground/90 leading-tight">
                {mood.label}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Insights & Metrics Dashboard */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reading Analytics */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5 bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-accent-purple/10 border border-accent-purple/20">
              <BarChart3 className="w-4 h-4 text-accent-purple" />
            </div>
            <div className="flex flex-col">
              <h4 className="text-sm font-semibold text-foreground">Reading DNA Analytics</h4>
              <span className="text-[10px] text-muted-foreground">Dynamic affinity distribution</span>
            </div>
          </div>

          <div className="flex flex-col gap-3.5 mt-2">
            {[
              { genre: "Fantasy & Magic", pct: 60, color: "var(--accent-purple)" },
              { genre: "Contemporary Romance", pct: 30, color: "var(--accent-pink)" },
              { genre: "Sci-Fi & Speculative", pct: 10, color: "var(--accent-gold)" },
            ].map((item) => (
              <div key={item.genre} className="flex flex-col gap-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">{item.genre}</span>
                  <span className="text-foreground/90">{item.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${item.pct}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    style={{ backgroundColor: item.color }} 
                    className="h-full rounded-full" 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sentiment Journal Status */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5 bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-accent-gold/10 border border-accent-gold/20">
              <TrendingUp className="w-4 h-4 text-accent-gold" />
            </div>
            <div className="flex flex-col">
              <h4 className="text-sm font-semibold text-foreground">Sentiment Summary</h4>
              <span className="text-[10px] text-muted-foreground">Based on your recent logs</span>
            </div>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-3">
            <div className="text-xs text-muted-foreground leading-relaxed">
              Your profile is currently tuned to <span className="text-accent-purple font-medium">Reflective & Cozy</span>. 
              The system is prioritizing slow-burn pacing, emotional depth, and heavy character growth in recommendations.
            </div>
            <div className="flex gap-2 mt-2">
              <span className="text-[10px] bg-accent-purple/10 border border-accent-purple/20 text-accent-purple px-2.5 py-0.5 rounded-full font-medium">Slow Burn (8/10)</span>
              <span className="text-[10px] bg-accent-pink/10 border border-accent-pink/20 text-accent-pink px-2.5 py-0.5 rounded-full font-medium">High Angst (4/10)</span>
              <span className="text-[10px] bg-accent-gold/10 border border-accent-gold/20 text-accent-gold px-2.5 py-0.5 rounded-full font-medium">Cozy Atmosphere</span>
            </div>
          </div>
        </div>
      </section>

      {/* Feed Placeholder Area */}
      <section className="border-t border-white/[0.05] pt-8 flex flex-col gap-4">
        <div className="flex flex-col gap-0.5">
          <h3 className="text-lg font-heading font-semibold text-foreground">Your Discovery Feed</h3>
          <p className="text-xs text-muted-foreground">Personalized matches appear here</p>
        </div>

        {/* Elegant Placeholder Screen */}
        <div className="border border-dashed border-white/10 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 bg-white/[0.005]">
          <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05] mb-2">
            <BookOpen className="w-5 h-5 text-muted-foreground/60" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">Feed Awaiting Vibe Selection</h4>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            Click one of the moods above or submit a journal log to initiate the semantic recommender and seed your visual discovery board.
          </p>
        </div>
      </section>
    </div>
  );
}

// ==========================================
// 2. RECOMMENDATIONS TAB VIEW
// ==========================================
function RecommendationsView() {
  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Curated Discoveries</h1>
        <p className="text-xs text-muted-foreground">Deep DNA matches generated by the semantic discovery pipeline</p>
      </div>

      {/* Filter shell (disabled/visual foundation only) */}
      <div className="glass-panel p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 bg-white/[0.01]">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="text-xs bg-white/[0.03] border border-white/[0.05] px-3.5 py-2 rounded-lg text-muted-foreground cursor-not-allowed">
            Genre: <span className="text-foreground font-semibold">Fantasy & Romance</span>
          </div>
          <div className="text-xs bg-white/[0.03] border border-white/[0.05] px-3.5 py-2 rounded-lg text-muted-foreground cursor-not-allowed">
            Pacing: <span className="text-foreground font-semibold">Slow Burn</span>
          </div>
          <div className="text-xs bg-white/[0.03] border border-white/[0.05] px-3.5 py-2 rounded-lg text-muted-foreground cursor-not-allowed">
            Spice: <span className="text-foreground font-semibold">Moderate</span>
          </div>
        </div>
        <div className="text-xs text-muted-foreground font-light italic">
          Showing 12 model templates
        </div>
      </div>

      {/* Premium card skeletons (visual layouts) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, idx) => (
          <div key={idx} className="glass-panel p-3.5 rounded-2xl flex flex-col gap-3 relative select-none bg-white/[0.01] hover:border-white/10 transition-colors duration-300">
            {/* Visual match badge */}
            <div className="absolute top-5 right-5 z-10 bg-accent-purple/90 backdrop-blur text-[10px] font-bold text-white px-2 py-0.5 rounded-md shadow-lg">
              98% Match
            </div>
            
            {/* Cover Box placeholder */}
            <div className="aspect-[2/3] w-full rounded-xl bg-white/[0.02] border border-white/[0.05] relative overflow-hidden animate-pulse flex items-center justify-center">
              <Compass className="w-8 h-8 text-white/[0.03]" />
            </div>

            {/* Tags placeholder */}
            <div className="flex gap-1.5 mt-1">
              <span className="h-4 w-14 rounded-full bg-white/[0.04] animate-pulse" />
              <span className="h-4 w-12 rounded-full bg-white/[0.04] animate-pulse" />
              <span className="h-4 w-16 rounded-full bg-white/[0.04] animate-pulse" />
            </div>

            {/* Metadata placeholders */}
            <div className="flex flex-col gap-2 mt-1">
              <div className="h-4 w-3/4 rounded bg-white/[0.06] animate-pulse" />
              <div className="h-3 w-1/2 rounded bg-white/[0.03] animate-pulse" />
            </div>

            {/* Rating placeholder */}
            <div className="h-3 w-1/3 rounded bg-white/[0.02] mt-auto animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================
// 3. COMPARE TAB VIEW
// ==========================================
function CompareView() {
  const dimensions = [
    { label: "Pacing (Slow Burn vs Kinetic)" },
    { label: "Emotional Depth" },
    { label: "Comfort Level" },
    { label: "Angst & Tension" },
    { label: "Humor & Wit" },
    { label: "World Building Complexity" },
  ];

  return (
    <div className="flex flex-col gap-8">
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

// ==========================================
// 4. SHELF TAB VIEW
// ==========================================
function ShelfView() {
  const shelfTabs = ["All Collection", "To Read", "Currently Reading", "Completed"];

  return (
    <div className="flex flex-col gap-8">
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
        {shelfTabs.map((tab, idx) => (
          <span 
            key={tab} 
            className={`pb-3 cursor-pointer transition-all duration-300 relative ${
              idx === 0 
                ? "text-accent-purple font-semibold" 
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
            {idx === 0 && (
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

// ==========================================
// 5. MOOD JOURNAL TAB VIEW
// ==========================================
function MoodView() {
  const recentLogs = [
    { date: "July 12, 2026", text: "Looking for an immersive escapist fantasy with beautiful prose, slow build romance, and high magic. No urban settings.", vibe: "Cozy & Immersive" },
    { date: "July 08, 2026", text: "Need something extremely fast-paced and gripping. A sci-fi space opera or thriller that keeps me up all night.", vibe: "High-Stakes Intense" },
  ];

  return (
    <div className="flex flex-col gap-8">
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
          <span className="text-[10px] text-muted-foreground/60 italic">
            AI analysis engine will extract DNA dimensions automatically
          </span>
          <Button disabled className="bg-gradient-purple-pink text-white rounded-full px-5 py-4 text-xs font-semibold cursor-not-allowed opacity-50">
            Submit Mood Log
          </Button>
        </div>
      </div>

      {/* History logs list */}
      <div className="flex flex-col gap-4 mt-2">
        <h4 className="text-xs font-bold text-muted-foreground/60 tracking-wider uppercase">Past Mood Logs</h4>
        
        <div className="flex flex-col gap-3">
          {recentLogs.map((log, idx) => (
            <div key={idx} className="glass-panel p-4 rounded-xl bg-white/[0.005] hover:bg-white/[0.01] transition-all flex flex-col sm:flex-row justify-between items-start gap-4 border-white/[0.04]">
              <div className="flex flex-col gap-1.5 flex-1">
                <span className="text-[10px] text-muted-foreground/50 font-semibold flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> {log.date}
                </span>
                <p className="text-xs text-muted-foreground/90 leading-relaxed font-sans font-light">
                  &ldquo;{log.text}&rdquo;
                </p>
              </div>
              <span className="text-[10px] bg-accent-purple/10 border border-accent-purple/20 text-accent-purple px-2.5 py-1 rounded-full font-medium shrink-0">
                Inferred: {log.vibe}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 6. FAVORITES TAB VIEW
// ==========================================
function FavoritesView() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Favorite Literature</h1>
        <p className="text-xs text-muted-foreground">A curated shelf of your absolute favorite books</p>
      </div>

      {/* Empty State skeleton grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, idx) => (
          <div key={idx} className="glass-panel p-3 rounded-2xl flex flex-col gap-2 relative bg-white/[0.005]">
            <Star className="w-4 h-4 text-accent-gold fill-accent-gold/20 absolute top-4 right-4 z-10" />
            <div className="aspect-[2/3] w-full rounded-lg bg-white/[0.02] border border-white/[0.05] animate-pulse flex items-center justify-center">
              <Star className="w-6 h-6 text-white/[0.02]" />
            </div>
            <div className="h-3.5 w-3/4 rounded bg-white/[0.06] animate-pulse mt-1" />
            <div className="h-3 w-1/2 rounded bg-white/[0.03] animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================
// 7. HISTORY TAB VIEW
// ==========================================
function HistoryView() {
  const historyItems = [
    { date: "Today", action: "Matched recommendation 'The Starless Sea' (98% match)" },
    { date: "Yesterday", action: "Compared 'The Hobbit' vs 'The Name of the Wind'" },
    { date: "July 10, 2026", action: "Logged new mood: 'Cozy fantasy vibes'" },
    { date: "July 08, 2026", action: "Added 'A Court of Thorns and Roses' to shelf" },
  ];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-heading font-bold text-gradient-gold">Discovery History</h1>
        <p className="text-xs text-muted-foreground">A timeline of your search requests, comparisons, and matching actions</p>
      </div>

      {/* Timeline Layout */}
      <div className="relative border-l border-white/[0.08] ml-4 pl-6 flex flex-col gap-6 mt-4">
        {historyItems.map((item, idx) => (
          <div key={idx} className="relative group">
            {/* Dot indicator */}
            <div className="absolute -left-[31px] top-1.5 w-2.5 h-2.5 rounded-full bg-white/[0.2] border-2 border-background group-hover:bg-accent-purple group-hover:scale-110 transition-all duration-300" />
            
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-muted-foreground/60 font-semibold">{item.date}</span>
              <p className="text-xs text-foreground/80 leading-relaxed">
                {item.action}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}