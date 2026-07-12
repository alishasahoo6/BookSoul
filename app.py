import html
import re
import textwrap
import base64
import os
import json

import streamlit as st
from booksoul.retrieval.google_books import fetch_book_info
from booksoul.generators.booksoul_generator import generate_booksoul
from booksoul.vector.embeddings import store_book_vector, retrieve_book_vector, collection
from booksoul.pipeline.recommender import get_semantic_recommendations, generate_recommendation_explanation
from booksoul.pipeline.comparator import compare_books, DIMENSIONS
from booksoul.ai.librarian import validate_book
from booksoul.models.book_dna import ensure_book_dna, get_dna_values

# ---------------------------------------------------------------------------
# Base64 Image Helper
# ---------------------------------------------------------------------------
def get_base64_image(image_path):
    """Loads a local image file and returns its base64 data URL."""
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception:
        return ""

# Pre-load background and assets as base64
HERO_LIBRARY_B64 = get_base64_image("assets/hero_library.png")
GLOWING_BOOK_B64 = get_base64_image("assets/glowing_book.png")
CASTLE_NIGHT_B64 = get_base64_image("assets/castle_night.png")

# ---------------------------------------------------------------------------
# Genre maps for display-time soul field resolution
# ---------------------------------------------------------------------------
_GENRE_VIBE_MAP = {
    "romance": "Cozy Romance", "fantasy": "Magical & Immersive",
    "horror": "Dark & Thrilling", "mystery": "Suspenseful",
    "thriller": "High-Stakes Intense", "science fiction": "Futuristic",
    "sci-fi": "Futuristic & Speculative", "self": "Motivational & Reflective",
    "habit": "Motivational & Reflective", "history": "Thoughtful & Informative",
    "biography": "Thoughtful & Informative", "memoir": "Intimate & Raw",
    "young adult": "Coming-of-Age & Electric", "ya": "Coming-of-Age & Electric",
    "adventure": "Pulse-Pounding & Wild", "literary": "Deeply Introspective",
    "drama": "Emotionally Charged", "love": "Heart-Warming & Tender",
    "contemporary": "Grounded & Relatable", "classic": "Timeless & Profound",
    "comedy": "Lighthearted & Witty", "humor": "Playful & Sharp",
    "psychological": "Mind-Bending & Tense", "crime": "Gritty & Gripping",
    "dystopian": "Unsettling & Provocative", "philosophy": "Meditative & Enlightening",
    "sport": "Driven & Competitive", "cook": "Warm & Sensory",
    "travel": "Wanderlust & Free-Spirited", "graphic": "Visual & Dynamic",
    "fiction": "Emotionally Rich & Story-Driven",
}
_GENRE_STYLE_MAP = {
    "romance": "Character-Driven & Emotional", "fantasy": "World-Building & Descriptive",
    "horror": "Atmospheric & Dread-Soaked", "mystery": "Suspense-Driven & Layered",
    "thriller": "Fast-Paced & Gripping", "science fiction": "Concept-Driven & Speculative",
    "sci-fi": "Concept-Driven & Speculative", "self": "Practical & Actionable",
    "habit": "Practical & Actionable", "history": "Narrative Non-Fiction",
    "biography": "Narrative Non-Fiction", "memoir": "Confessional & Intimate",
    "young adult": "Voice-Driven & Visceral", "ya": "Voice-Driven & Visceral",
    "adventure": "Kinetic & Propulsive", "literary": "Lyrical & Deliberate",
    "drama": "Nuanced & Character-Focused", "love": "Sensory & Heartfelt",
    "contemporary": "Conversational & Authentic", "classic": "Elegant & Measured",
    "comedy": "Breezy & Witty", "humor": "Sharp & Irreverent",
    "psychological": "Unreliable & Twisting", "crime": "Terse & Investigative",
    "dystopian": "Bleak & Urgent", "philosophy": "Dense & Thought-Provoking",
    "fiction": "Immersive & Vividly Drawn",
}

def resolve_field(value, themes, genre_map, fallback):
    """Return value unless it is Unknown/N/A/empty, then infer from themes."""
    if value and value not in ("Unknown", "N/A", ""):
        return value
    text = " ".join(themes).lower()
    for keyword, label in genre_map.items():
        if keyword in text:
            return label
    return fallback

_TAG_RE = re.compile(r"<[^>]*>")
_WHITESPACE_RE = re.compile(r"\s+")

def clean_display_text(value, fallback=""):
    """Normalize model/cache text so escaped HTML never reaches the UI as source."""
    if value is None:
        return fallback
    if isinstance(value, (list, tuple, set)):
        value = ", ".join(clean_display_text(item) for item in value if item)
    text = str(value)
    for _ in range(2):
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped
    text = re.sub(r"(?i)<\s*br\s*/?\s*>", " ", text)
    text = re.sub(r"(?i)</\s*(p|div|li|span|strong|em|b|i)\s*>", " ", text)
    text = _TAG_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or fallback

def escape_display_text(value, fallback=""):
    return html.escape(clean_display_text(value, fallback), quote=True)

def smart_truncate(text, max_length=280, complete_sentences=True):
    """Truncate text at word boundary, optionally trying to complete the sentence."""
    if len(text) <= max_length:
        return text
    if not complete_sentences:
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:
            return text[:last_space] + "."
        return truncated + "."
    search_window = min(len(text), max_length + 150)
    truncated = text[:search_window]
    for ending in ['. ', '! ', '? ', '.', '!', '?']:
        idx = truncated.rfind(ending)
        if idx > max_length * 0.75 and idx != -1:
            return text[:idx + len(ending)]
    last_space = text[:max_length].rfind(' ')
    if last_space > max_length * 0.7:
        return text[:last_space] + "."
    return text[:max_length] + "."

def normalize_categories(categories):
    """Convert Google Books categories into human-friendly format."""
    if not categories:
        return "General"
    if isinstance(categories, str):
        categories = [categories]
    
    category_mapping = {
        "fiction": "Fiction", "romance": "Romance", "mystery": "Mystery & Thriller",
        "thriller": "Mystery & Thriller", "fantasy": "Fantasy & Magic",
        "science fiction": "Sci-Fi & Technology", "sci-fi": "Sci-Fi & Technology",
        "horror": "Horror & Suspense", "biography": "Biography & Memoir",
        "memoir": "Biography & Memoir", "history": "History & Culture",
        "travel": "Travel & Adventure", "adventure": "Travel & Adventure",
        "self-help": "Personal Development", "health": "Health & Wellness",
        "young adult": "Young Adult", "juvenile": "Children's",
        "relationships": "Relationships & Romance", "man-woman": "Relationships & Romance",
        "comic": "Comics & Graphic Novels", "graphic": "Comics & Graphic Novels",
        "poetry": "Poetry & Literature", "literary": "Literary Fiction",
    }
    
    normalized = set()
    for cat in categories:
        cat_lower = cat.lower().strip()
        for key, value in category_mapping.items():
            if key in cat_lower:
                normalized.add(value)
                break
        else:
            normalized.add(cat.strip())
    result = sorted(list(normalized), key=lambda x: x not in category_mapping.values())[:2]
    return " · ".join(result) if result else "General"

def render_badge(value, badge_type="trope", icon=""):
    label = escape_display_text(value)
    if not label:
        return ""
    badge_type = badge_type if badge_type in {"vibe", "style", "trope"} else "trope"
    prefix = f"{icon} " if icon else ""
    return f'<span class="badge badge-{badge_type}">{prefix}{label}</span>'

def render_badge_group(values, badge_type="trope", icon="", limit=None):
    if not values:
        return ""
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    values = list(values)[:limit] if limit else list(values)
    return "".join(render_badge(value, badge_type, icon) for value in values)

def render_book_badges(soul, themes=None, trope_limit=4):
    """Return the shared visual badge HTML used by recommendation cards."""
    themes = themes or []
    vibe = resolve_field(soul.get("reader_vibe", ""), themes, _GENRE_VIBE_MAP, "Emotionally Resonant")
    style = resolve_field(soul.get("writing_style", ""), themes, _GENRE_STYLE_MAP, "Richly Layered")
    primary_badges = render_badge(vibe, "vibe", "🧬") + render_badge(style, "style", "✍️")
    trope_badges = render_badge_group(soul.get("tropes", []), "trope", limit=trope_limit)
    trope_group = f'<div style="margin-bottom:8px; display:flex; flex-wrap:wrap; gap:4px;">{trope_badges}</div>' if trope_badges else ""
    return f'<div style="margin-bottom:8px; display:flex; flex-wrap:wrap; gap:4px;">{primary_badges}</div>{trope_group}'

def render_book_dna(soul, description="", categories=None):
    if not isinstance(soul, dict):
        soul = {}
    ensure_book_dna(soul, description=description, categories=categories)
    dna_values = get_dna_values(soul.get("dna", {}))
    if not dna_values.get("atmosphere"):
        dna_values["atmosphere"] = clean_display_text(
            soul.get("emotional_tone") or soul.get("reader_vibe") or "Balanced", "Balanced"
        )
    dna_labels = {
        "emotional_depth": "Emotional Depth", "comfort": "Comfort", "humor": "Humor",
        "angst": "Angst", "spice": "Spice", "character_growth": "Character Growth", "pacing": "Pacing",
    }
    rows = []
    for key, label in dna_labels.items():
        filled = int(max(0, min(10, dna_values.get(key, 5))))
        rows.append(
            '<div class="dna-row">'
            f'<span class="dna-label">{escape_display_text(label)}</span>'
            '<span class="dna-track">'
            f'<span class="dna-fill" style="width:{filled * 10}%;"></span>'
            '</span>'
            f'<span class="dna-score">{filled}/10</span>'
            '</div>'
        )
    atmosphere = escape_display_text(dna_values.get("atmosphere", "Balanced"))
    return (
        '<div class="dna-panel">'
        '<div class="dna-title">BookSoul DNA</div>'
        f'{"".join(rows)}'
        f'<div class="dna-atmosphere">Atmosphere: {atmosphere}</div>'
        '</div>'
    )

# ============================================================
# PAGE CONFIG & INITIAL STATE
# ============================================================
st.set_page_config(
    page_title="BookSoul · Books that understand you.",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State Variables
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []
if "search_history" not in st.session_state:
    st.session_state["search_history"] = []
if "mood_logs" not in st.session_state:
    st.session_state["mood_logs"] = []

# Set Default Taste Profile immediately so app looks fully populated at first glance
if "profile" not in st.session_state:
    st.session_state["profile"] = {
        "age_group": "👩 18–24",
        "content_level": "💕 Mild Romance",
        "genres": ["Fantasy", "Romance"],
        "spice_level": "Moderate",
        "pacing_level": "Slow Burn",
        "mood_query": ""
    }
    st.session_state["onboarding_done"] = True

# Read tab from URL query params
params = st.query_params
active_tab = params.get("tab", "Home")
st.session_state["active_tab"] = active_tab

# Navigation Helper
def navigate_to(tab_name, **kwargs):
    st.query_params.clear()
    st.query_params["tab"] = tab_name
    for k, v in kwargs.items():
        if v:
            st.query_params[k] = str(v)
    st.session_state["active_tab"] = tab_name
    st.rerun()

# ============================================================
# GLOBAL CSS — Premium Dark Glassmorphism Theme
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&display=swap');

:root {{
  --bg:          #08090d;
  --surface:     #0d0e15;
  --card:        #151722;
  --glass:       rgba(255,255,255,0.03);
  --glass-hover: rgba(255,255,255,0.06);
  --border:      rgba(255,255,255,0.05);
  --accent-purple: #a78bfa;
  --accent-pink:   #f472b6;
  --accent-gold:   #e2c299;
  --text-primary:  #f1f5f9;
  --text-muted:    #94a3b8;
  --radius:      16px;
  --shadow:      0 8px 32px rgba(0,0,0,0.45);
}}

/* Hide Streamlit Default UI Elements */
[data-testid="stHeader"], footer, #MainMenu {{
    display: none !important;
}}
[data-testid="block-container"] {{
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
}}

/* Base Styling */
html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg) !important;
  font-family: 'Inter', sans-serif !important;
  color: var(--text-primary) !important;
}}

/* Custom Scrollbars */
::-webkit-scrollbar {{
  width: 8px;
  height: 8px;
}}
::-webkit-scrollbar-track {{
  background: var(--bg);
}}
::-webkit-scrollbar-thumb {{
  background: var(--card);
  border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
  background: var(--accent-purple);
}}

/* Typography */
h1, h2, h3, h4 {{
  font-family: 'Playfair Display', serif !important;
  color: var(--text-primary) !important;
}}
p, span, label, div {{
  color: var(--text-primary) !important;
}}

/* Sidebar Container (Sticky Left-Column) */
.sidebar-sticky {{
  position: -webkit-sticky;
  position: sticky;
  top: 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 25px;
}}

/* Logo Section */
.logo-container {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.logo-text {{
  font-family: 'Playfair Display', serif;
  font-size: 2.1rem;
  font-weight: 700;
  color: var(--accent-gold);
  letter-spacing: -0.02em;
}}
.logo-tagline {{
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 400;
  letter-spacing: 0.02em;
}}

/* Navigation Menu */
.nav-menu {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.nav-item {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: var(--text-muted) !important;
  text-decoration: none !important;
  border-radius: 10px;
  font-weight: 500;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}}
.nav-item:hover {{
  background: var(--glass-hover);
  color: var(--text-primary) !important;
}}
.nav-item.active {{
  background: #1b132c;
  color: var(--accent-purple) !important;
  font-weight: 600;
  border-left: 3px solid var(--accent-purple);
}}

/* Taste Profile Section */
.taste-profile {{
  border-top: 1px solid var(--border);
  padding-top: 20px;
}}
.taste-profile-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}
.taste-profile-title {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-muted);
}}
.taste-edit-link {{
  font-size: 0.75rem;
  color: var(--accent-purple) !important;
  text-decoration: none !important;
  font-weight: 600;
}}
.taste-edit-link:hover {{
  text-decoration: underline !important;
}}
.taste-pills {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.taste-pill {{
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.82rem;
  color: var(--text-muted);
}}

/* Sidebar Quote */
.quote-container {{
  border-top: 1px solid var(--border);
  padding-top: 20px;
  text-align: center;
}}
.quote-label {{
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--accent-gold);
  display: block;
  margin-bottom: 8px;
}}
.quote-text {{
  font-size: 0.82rem;
  font-style: italic;
  line-height: 1.5;
  color: var(--text-muted);
  margin: 0;
}}

/* Hero Layout (Split view in mockup) */
.hero-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow);
  margin-bottom: 30px;
}}
.hero-left {{
  flex: 1.2;
}}
.hero-right {{
  flex: 0.8;
  display: flex;
  justify-content: flex-end;
}}
.hero-title {{
  font-family: 'Playfair Display', serif;
  font-size: 2.6rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 12px;
}}
.hero-subtitle {{
  color: var(--text-muted);
  font-size: 1.05rem;
  margin-bottom: 25px;
  font-weight: 300;
}}
.tag-pill {{
  display: inline-block;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 50px;
  padding: 6px 14px;
  font-size: 0.82rem;
  color: var(--text-muted) !important;
  text-decoration: none !important;
  margin-right: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}}
.tag-pill:hover {{
  background: rgba(167, 139, 250, 0.1);
  border-color: var(--accent-purple);
  color: var(--accent-purple) !important;
}}

/* Popular Moods Section */
.mood-grid {{
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 12px;
  margin-top: 15px;
  margin-bottom: 30px;
}}
.mood-card-custom {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 10px;
  text-align: center;
  text-decoration: none !important;
  color: var(--text-muted) !important;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}}
.mood-card-custom:hover {{
  background: rgba(167, 139, 250, 0.06);
  border-color: var(--accent-purple);
  color: var(--text-primary) !important;
  transform: translateY(-2px);
}}
.mood-icon-custom {{
  font-size: 1.5rem;
  color: var(--accent-purple);
}}
.mood-label-custom {{
  font-size: 0.78rem;
  font-weight: 500;
}}

/* Recommended Section */
.section-header-custom {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}}
.rec-grid-custom {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}}
.book-card-custom {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 12px;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
  box-shadow: var(--shadow);
  height: 100%;
}}
.book-card-custom:hover {{
  border-color: rgba(167, 139, 250, 0.3);
  transform: translateY(-3px);
}}
.cover-wrap-custom {{
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 12px;
}}
.cover-img-custom {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}
.match-badge-custom {{
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(167, 139, 250, 0.95);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}}
.book-title-custom {{
  font-family: 'Playfair Display', serif;
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--text-primary);
  line-height: 1.3;
}}
.book-author-custom {{
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}}
.stars-rating-custom {{
  font-size: 0.8rem;
  color: #d4af37;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: auto;
  padding-top: 8px;
}}

/* Badge Chips */
.badge {{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 500;
  margin: 2px 2px;
}}
.badge-vibe  {{ background: rgba(167, 139, 250, 0.12); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.2); }}
.badge-style {{ background: rgba(244, 114, 182, 0.12); color: #f9a8d4; border: 1px solid rgba(244, 114, 182, 0.2); }}
.badge-trope {{ background: rgba(52, 211, 153, 0.1);  color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.18); }}

/* Split Row bottom */
.journey-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  height: 140px;
  display: flex;
  align-items: center;
  gap: 15px;
}}
.insight-card {{
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow);
  height: 140px;
  background-size: cover;
  background-position: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
}}
.insight-label {{
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent-gold);
  margin-bottom: 6px;
}}
.insight-title {{
  font-family: 'Playfair Display', serif;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 4px;
}}
.insight-text {{
  font-size: 0.8rem;
  color: var(--text-muted);
}}

/* Custom Form elements for styling */
[data-testid="stTextInput"] input {{
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  padding: 12px 16px !important;
}}
[data-testid="stTextInput"] input:focus {{
  border-color: var(--accent-purple) !important;
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2) !important;
}}

[data-testid="stButton"] button {{
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink)) !important;
  color: white !important;
  border: none !important;
  border-radius: 50px !important;
  font-weight: 600 !important;
  padding: 10px 24px !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 4px 15px rgba(167, 139, 250, 0.25) !important;
}}
[data-testid="stButton"] button:hover {{
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(167, 139, 250, 0.4) !important;
}}

/* Recommendation Row Cards */
.recs-card-horizontal {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  margin-bottom: 1.2rem;
  box-shadow: var(--shadow);
}}
.dna-panel {{
  margin: 12px 0 10px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(0,0,0,0.2);
}}
.dna-title {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent-purple);
  margin-bottom: 8px;
}}
.dna-row {{
  display: grid;
  grid-template-columns: minmax(120px, 170px) 1fr 42px;
  align-items: center;
  gap: 10px;
  margin: 5px 0;
}}
.dna-label {{
  color: var(--text-muted);
  font-size: 0.78rem;
}}
.dna-track {{
  height: 6px;
  border-radius: 99px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}}
.dna-fill {{
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--accent-purple), var(--accent-pink));
}}
.dna-score {{
  color: var(--text-primary);
  font-size: 0.76rem;
  font-weight: 600;
  text-align: right;
}}
.dna-atmosphere {{
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 0.8rem;
}}

.soul-match-wrap {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0 14px;
}}
.soul-match-label {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent-purple);
  white-space: nowrap;
}}
.soul-match-bar-bg {{
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 99px;
  overflow: hidden;
}}
.soul-match-bar-fill {{
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--accent-purple), var(--accent-pink));
}}
.soul-match-pct {{
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent-purple);
  min-width: 38px;
  text-align: right;
}}
.match-reason {{
  background: linear-gradient(135deg, rgba(167,139,250,0.08), rgba(244,114,182,0.06));
  border-left: 3px solid var(--accent-purple);
  border-radius: 0 10px 10px 0;
  padding: 10px 14px;
  margin-top: 10px;
  font-size: 0.88rem;
  color: var(--text-muted) !important;
  line-height: 1.6;
}}
.rank-num {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink));
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
  margin-right: 8px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(167,139,250,0.4);
}}

/* Onboarding Wizard */
.ob-card-custom {{
  max-width: 600px;
  margin: 40px auto;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px;
  box-shadow: var(--shadow);
}}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LAYOUT STRUCTURE
# ============================================================
col_sidebar, col_main = st.columns([1.1, 3.8], gap="large")

# ------------------------------------------------------------
# LEFT COLUMN: SIDEBAR
# ------------------------------------------------------------
with col_sidebar:
    profile = st.session_state.get("profile", {})
    genres_str = ", ".join(profile.get("genres", []))
    
    # Custom HTML Sidebar
    st.markdown(f"""
    <div class="sidebar-sticky">
      <div class="logo-container">
        <span class="logo-text">Book<span style="font-style: italic; font-family: 'Playfair Display'; color: #a78bfa;">Soul</span></span>
        <span class="logo-tagline">Books that understand you.</span>
      </div>
      
      <div class="nav-menu">
        <a href="?tab=Home" target="_self" class="nav-item {"active" if active_tab == 'Home' else ''}">🏠 Home</a>
        <a href="?tab=Search" target="_self" class="nav-item {"active" if active_tab == 'Search' else ''}">🔍 Search</a>
        <a href="?tab=Recommendations" target="_self" class="nav-item {"active" if active_tab == 'Recommendations' else ''}">🔮 Recommendations</a>
        <a href="?tab=Compare" target="_self" class="nav-item {"active" if active_tab == 'Compare' else ''}">⚖️ Compare Books</a>
        <a href="?tab=Shelf" target="_self" class="nav-item {"active" if active_tab == 'Shelf' else ''}">📚 My Shelf</a>
        <a href="?tab=Mood" target="_self" class="nav-item {"active" if active_tab == 'Mood' else ''}">📝 Mood Journal</a>
        <a href="?tab=Favorites" target="_self" class="nav-item {"active" if active_tab == 'Favorites' else ''}">❤️ Favorites ({len(st.session_state["favorites"])})</a>
        <a href="?tab=History" target="_self" class="nav-item {"active" if active_tab == 'History' else ''}">🕒 History</a>
      </div>
      
      <div class="taste-profile">
        <div class="taste-profile-header">
          <span class="taste-profile-title">YOUR TASTE PROFILE</span>
          <a href="?tab=Onboarding" target="_self" class="taste-edit-link">✏️ Edit</a>
        </div>
        <div class="taste-pills">
          <div class="taste-pill">👤 Age: {profile.get("age_group", "18-24")}</div>
          <div class="taste-pill">🧸 Comfort: {profile.get("content_level", "Mild")}</div>
          <div class="taste-pill">🎭 Genres: {genres_str if genres_str else "Any"}</div>
          <div class="taste-pill">🌶️ Spice: {profile.get("spice_level", "Moderate")}</div>
          <div class="taste-pill">⏱️ Pacing: {profile.get("pacing_level", "Slow Burn")}</div>
        </div>
      </div>
      
      <div class="quote-container">
        <span class="quote-label">✦ BOOKSOUL QUOTE ✦</span>
        <p class="quote-text">"Sometimes the right book finds you at the right time."</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Glowing book asset
    if GLOWING_BOOK_B64:
        st.markdown(f'<img src="{GLOWING_BOOK_B64}" style="width: 100%; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 20px rgba(167,139,250,0.15); border: 1px solid var(--border);">', unsafe_allow_html=True)
    else:
        st.image("assets/glowing_book.png", use_container_width=True)

# ------------------------------------------------------------
# RIGHT COLUMN: MAIN CONTENT
# ------------------------------------------------------------
with col_main:
    
    # ── VIEW: ONBOARDING WIZARD ──────────────────────────────
    if active_tab == "Onboarding":
        st.markdown("""
        <div class="ob-card-custom">
          <div style="text-align: center; margin-bottom: 25px;">
            <h2 style="font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #a78bfa, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🔮 Personalise Your BookSoul</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 8px;">Let us configure your profile to recommend stories matched perfectly to your soul.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        # We can implement the multi-step onboarding wizard
        with st.form("onboarding_form"):
            ob_age = st.radio("🎂 Which age group best describes you?", ["👧 Under 13","🧒 13–15","🧑 16–17","👩 18–24","👨 25–34","👵 35+"], index=3)
            ob_comfort = st.radio("🧸 Which content level are you comfortable reading?", [
                "🌼 Family Friendly — No explicit content, minimal violence",
                "💕 Mild Romance — Kissing & romance, fade-to-black only",
                "❤️ Mature Romance — Explicit romance (spice), adult readers"
            ], index=1)
            
            _GENRES_LIST = ["Romance","Fantasy","Mystery","Thriller","Historical Fiction","Science Fiction","Horror","Young Adult","Non-fiction","Biography"]
            ob_genres = st.multiselect("🎭 Select your favorite genres:", _GENRES_LIST, default=["Fantasy", "Romance"])
            
            ob_spice = st.select_slider("🌶️ Desired Romance Spice Level:", options=["None", "Mild", "Moderate", "High"], value="Moderate")
            ob_pacing = st.select_slider("⏱️ Preferred Story Pacing:", options=["Slow Burn", "Medium", "Fast-Paced"], value="Slow Burn")
            
            ob_query = st.text_input("📝 Describe what you're looking for (optional):", placeholder="e.g. cozy workplace romance with slow burn tension")
            
            submit_ob = st.form_submit_button("✨ Save & Start Discovering")
            if submit_ob:
                st.session_state["profile"] = {
                    "age_group": ob_age,
                    "content_level": ob_comfort.split("—")[0].strip(),
                    "genres": ob_genres,
                    "spice_level": ob_spice,
                    "pacing_level": ob_pacing,
                    "mood_query": ob_query
                }
                st.session_state["onboarding_done"] = True
                if ob_query.strip():
                    navigate_to("Recommendations", query=ob_query.strip())
                else:
                    navigate_to("Home")

    # ── VIEW: HOME ──────────────────────────────────────────
    elif active_tab == "Home":
        # Top Header (Avatar Greeting)
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 20px; gap: 15px;">
          <button style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-muted);">🔔</button>
          <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 6px 14px; border-radius: 50px;">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #a78bfa, #f472b6); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold;">R</div>
            <span style="font-size: 0.88rem; font-weight: 500; color: var(--text-primary);">Hello, Reader ▼</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hero Split layout
        col_hero_left, col_hero_right = st.columns([1.3, 0.7], gap="medium")
        with col_hero_left:
            st.markdown("""
            <h1 style="font-size: 2.8rem; font-weight: 700; line-height: 1.25; margin-bottom: 12px; font-family: 'Playfair Display', serif;">
              What kind of story <br><span style="font-style: italic; font-family: 'Playfair Display'; color: #a78bfa;">soul</span> are you looking for today?
            </h1>
            <p style="color: var(--text-muted); font-size: 1.05rem; margin-bottom: 25px; font-weight: 300;">
              Describe your mood, a book you loved, or the vibe you want to feel.
            </p>
            """, unsafe_allow_html=True)
            
            # Simple functional search text input
            col_search_input, col_search_btn = st.columns([4, 1])
            with col_search_input:
                h_query = st.text_input("mood_query", placeholder="I'm in the mood for something like...", label_visibility="collapsed", key="home_query_input")
            with col_search_btn:
                h_search = st.button("🔮 Search", key="home_search_submit_btn", use_container_width=True)
                if h_search and h_query:
                    # Save to search history
                    if h_query.strip() not in st.session_state["search_history"]:
                        st.session_state["search_history"].append(h_query.strip())
                    navigate_to("Recommendations", query=h_query.strip())
            
            st.markdown("""
            <div style="margin-top: 15px;">
              <span style="color: var(--text-muted); font-size: 0.85rem; margin-right: 10px;">Try something like:</span>
              <a href="?tab=Recommendations&query=A+cozy+fantasy+with+found+family" target="_self" class="tag-pill">A cozy fantasy with found family</a>
              <a href="?tab=Recommendations&query=Books+like+Verity" target="_self" class="tag-pill">Books like Verity</a>
              <a href="?tab=Recommendations&query=Enemies+to+lovers" target="_self" class="tag-pill">Enemies to lovers</a>
              <a href="?tab=Recommendations&query=Heartbreaking+romance" target="_self" class="tag-pill">Heartbreaking romance</a>
            </div>
            """, unsafe_allow_html=True)
            
        with col_hero_right:
            if HERO_LIBRARY_B64:
                st.markdown(f'<img src="{HERO_LIBRARY_B64}" style="width: 100%; border-radius: 16px; box-shadow: var(--shadow); border: 1px solid var(--border);">', unsafe_allow_html=True)
            else:
                st.image("assets/hero_library.png", use_container_width=True)
                
        # Popular Moods Section
        st.markdown("""
        <div class="mood-container">
          <div class="mood-header">
            <div>
              <div class="mood-title">Popular Moods</div>
              <div class="mood-subtitle">What readers are searching for</div>
            </div>
            <a href="?tab=Recommendations" target="_self" style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 50px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; text-decoration: none !important; color: var(--text-primary) !important;">View all</a>
          </div>
          <div class="mood-grid">
            <a href="?tab=Recommendations&query=Slow+Burn" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">⏳</span>
              <span class="mood-label-custom">Slow Burn</span>
            </a>
            <a href="?tab=Recommendations&query=Enemies+to+Lovers" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">⚔️</span>
              <span class="mood-label-custom">Enemies to Lovers</span>
            </a>
            <a href="?tab=Recommendations&query=Found+Family" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">👥</span>
              <span class="mood-label-custom">Found Family</span>
            </a>
            <a href="?tab=Recommendations&query=Dark+Academia" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">🏛️</span>
              <span class="mood-label-custom">Dark Academia</span>
            </a>
            <a href="?tab=Recommendations&query=Forced+Proximity" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">🔄</span>
              <span class="mood-label-custom">Forced Proximity</span>
            </a>
            <a href="?tab=Recommendations&query=He+Falls+First" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">👑</span>
              <span class="mood-label-custom">He Falls First</span>
            </a>
            <a href="?tab=Recommendations&query=Touch+Her+and+Die" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">💀</span>
              <span class="mood-label-custom">Touch Her and Die</span>
            </a>
            <a href="?tab=Recommendations&query=Morally+Grey+Hero" target="_self" class="mood-card-custom">
              <span class="mood-icon-custom">🎭</span>
              <span class="mood-label-custom">Morally Grey Hero</span>
            </a>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommended For You Section
        st.markdown("""
        <div class="section-header-custom">
          <div>
            <h3 style="font-size: 1.4rem; font-weight: 700; font-family: 'Playfair Display', serif; margin: 0;">Recommended For You</h3>
            <span style="color: var(--text-muted); font-size: 0.85rem;">Books picked just for your soul</span>
          </div>
          <a href="?tab=Recommendations" target="_self" style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 50px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; text-decoration: none !important; color: var(--text-primary) !important;">View all recommendations</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Fetch the pre-seeded mockup books
        mockup_ids = ["wildlove", "powerless", "fourthwing", "acourtofthornsandroses"]
        res_mockup = collection.get(ids=mockup_ids, include=["metadatas"])
        
        if res_mockup and res_mockup.get("metadatas"):
            meta_map = {id_: meta for id_, meta in zip(res_mockup["ids"], res_mockup["metadatas"])}
            rec_cols = st.columns(4, gap="medium")
            
            # Curated details mapping for matches to display exactly like the mockup image
            curated_details = {
                "wildlove": {
                    "match": 96, "rating": 4.6,
                    "badges": ['Small Town', 'Slow Burn', 'Protective Hero'],
                    "explanation": "Wild Love has a slow pacing (4/10) matching your Slow Burn preference, cozy emotional depth, and a tender, comforting small town atmosphere."
                },
                "powerless": {
                    "match": 94, "rating": 4.5,
                    "badges": ['Enemies to Lovers', 'Slow Burn', 'High Stakes'],
                    "explanation": "Powerless features high-stakes action and classic enemies-to-lovers tension with slow pacing (5/10) that aligns perfectly with your Slow Burn taste."
                },
                "fourthwing": {
                    "match": 93, "rating": 4.7,
                    "badges": ['Fantasy', 'Dragons', 'Strong FMC'],
                    "explanation": "Fourth Wing offers a highly immersive magical fantasy world, a strong female lead character, dragon bonding, and high angst and spice."
                },
                "acourtofthornsandroses": {
                    "match": 92, "rating": 4.6,
                    "badges": ['Fantasy', 'Romance', 'Faerie World'],
                    "explanation": "A Court of Thorns and Roses blends magical fantasy world building with slow-burn romance in a rich, dangerous faerie court setting."
                }
            }
            
            for i, b_id in enumerate(mockup_ids):
                if b_id in meta_map:
                    meta = meta_map[b_id]
                    title = meta.get("title", "Untitled")
                    authors = meta.get("authors", "Unknown")
                    cover = meta.get("cover_image", "")
                    details = curated_details.get(b_id, {"match": 90, "rating": 4.5, "badges": ["Fantasy"], "explanation": ""})
                    
                    with rec_cols[i]:
                        # Favorite state
                        is_fav = title in st.session_state["favorites"]
                        fav_btn_label = "❤️" if is_fav else "🖤"
                        
                        cover_html = f'<img src="{cover}" class="cover-img-custom">' if cover else '<div style="width:100%; height:100%; background:var(--card); display:flex; align-items:center; justify-content:center; font-size:2rem;">📖</div>'
                        
                        # Render card top
                        st.markdown(f"""
                        <div class="book-card-custom">
                          <div class="cover-wrap-custom">
                            {cover_html}
                            <span class="match-badge-custom">{details['match']}% Match</span>
                          </div>
                          <div class="book-title-custom">{title}</div>
                          <div class="book-author-custom">by {authors}</div>
                          <div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;">
                            {"".join(f'<span class="badge badge-vibe">{tag}</span>' for tag in details['badges'])}
                          </div>
                          <div class="stars-rating-custom">⭐⭐⭐⭐⭐ {details['rating']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Heart Toggle and Why This Matches Expander
                        col_fav, col_exp = st.columns([1, 4])
                        with col_fav:
                            if st.button(fav_btn_label, key=f"fav_home_{b_id}"):
                                if is_fav:
                                    st.session_state["favorites"].remove(title)
                                else:
                                    st.session_state["favorites"].append(title)
                                st.rerun()
                        with col_exp:
                            with st.expander("Why this matches", expanded=False):
                                st.markdown(f'<div style="font-size:0.8rem; color:var(--text-muted); line-height:1.5;">{details["explanation"]}</div>', unsafe_allow_html=True)
        else:
            st.warning("Database seeding not completed yet or failed. Please check the database.")

        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        # Bottom split row: Continue journey & Insight
        col_journey, col_insight = st.columns(2, gap="large")
        with col_journey:
            # Continue Journey card
            st.markdown("""
            <div style="font-size: 1.15rem; font-weight: 700; font-family: 'Playfair Display', serif; margin-bottom: 10px;">Continue Your Journey</div>
            """, unsafe_allow_html=True)
            
            res_tog = collection.get(ids=["throneofglass"], include=["metadatas"])
            tog_cover = ""
            if res_tog and res_tog.get("metadatas"):
                tog_cover = res_tog["metadatas"][0].get("cover_image", "")
            
            tog_cover_html = f'<img src="{tog_cover}" style="height: 100px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.4);">' if tog_cover else '<div style="width: 70px; height: 100px; background: var(--card); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; border-radius: 8px;">📖</div>'
            
            st.markdown(f"""
            <div class="journey-card">
              {tog_cover_html}
              <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">Throne of Glass</div>
                <div style="color: var(--text-muted); font-size: 0.82rem; margin-bottom: 12px;">Sarah J. Maas</div>
                <div style="display: flex; align-items: center; gap: 10px;">
                  <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 10px; overflow: hidden;">
                    <div style="width: 65%; height: 100%; background: linear-gradient(90deg, var(--accent-purple), var(--accent-pink)); border-radius: 10px;"></div>
                  </div>
                  <span style="font-size: 0.78rem; font-weight: 600; color: var(--accent-purple);">65%</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_insight:
            # BookSoul Insight Card with Castle Background as base64
            st.markdown("""
            <div style="font-size: 1.15rem; font-weight: 700; font-family: 'Playfair Display', serif; margin-bottom: 10px;">BookSoul Insight</div>
            """, unsafe_allow_html=True)
            
            bg_style = f"background-image: linear-gradient(rgba(20, 22, 32, 0.88), rgba(20, 22, 32, 0.88)), url('{CASTLE_NIGHT_B64}');" if CASTLE_NIGHT_B64 else "background-color: var(--surface);"
            st.markdown(f"""
            <div class="insight-card" style="{bg_style}">
              <div class="insight-label">BOOKSOUL INSIGHT</div>
              <div class="insight-title">You're in a <span style="color: var(--accent-purple);">slow burn</span> era.</div>
              <div class="insight-text">You love tension that takes time. The payoff is your favorite part.</div>
            </div>
            """, unsafe_allow_html=True)

    # ── VIEW: RECOMMENDATIONS ────────────────────────────────
    elif active_tab == "Recommendations":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 20px;">🔮 Ask BookSoul for Recommendations</h2>', unsafe_allow_html=True)
        
        # Check if query is in URL query parameters
        rec_query = params.get("query", "")
        
        col_rec_input, col_rec_btn = st.columns([5, 1])
        with col_rec_input:
            recommend_query = st.text_input(
                "Search Recommendations",
                value=rec_query,
                placeholder="e.g. cozy workplace romance with slow burn tension  ·  dark academia mystery  ·  books like Wild Love",
                label_visibility="collapsed",
                key="rec_search_query_input"
            )
        with col_rec_btn:
            search_clicked = st.button("🔮 Search", key="rec_search_submit_btn", use_container_width=True)
            
        if search_clicked:
            print("=== SEARCH BUTTON CLICKED ===")
            if recommend_query.strip() not in st.session_state["search_history"]:
                st.session_state["search_history"].append(recommend_query.strip())
                
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(
                '<div class="ai-thinking" style="padding: 12px; background: rgba(167,139,250,0.08); border-radius: 8px; border: 1px solid rgba(167,139,250,0.2); font-size: 0.9rem; color: var(--accent-purple); display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px;">'
                '<div class="ai-dot"></div><div class="ai-dot"></div><div class="ai-dot"></div>'
                '&nbsp; BookSoul is reading between the lines…'
                '</div>',
                unsafe_allow_html=True
            )
            with st.spinner("Consulting the AI Librarian..."):
                print("=== SEARCH BUTTON CLICKED ===")
                matches = get_semantic_recommendations(recommend_query.strip(), n_results=5)
                print("=== SEARCH FINISHED ===")
            thinking_placeholder.empty()
            
            if matches:
                st.markdown(f"""
                <div class="stat-strip" style="background: var(--glass); border: 1px solid var(--border); padding: 10px 16px; border-radius: 50px; display: inline-flex; gap: 15px; margin-bottom: 20px; font-size: 0.85rem; color: var(--text-muted);">
                  <span>🎯 Found <strong>{len(matches)}</strong> matches</span>
                  <span>🔎 Query: <strong>{escape_display_text(recommend_query)}</strong></span>
                  <span>📡 Source: internet + vector DB</span>
                </div>
                """, unsafe_allow_html=True)
                
                for index, match in enumerate(matches, 1):
                    soul          = match.get("soul", {})
                    themes        = soul.get("themes", [])
                    soul_match    = match.get("soul_match", 0)
                    match_reasons = match.get("match_reasons", [])
                    description   = match.get("description", "")
                    
                    try:
                        soul_match = max(0, min(100, int(float(soul_match))))
                    except (TypeError, ValueError):
                        soul_match = 0
                    
                    title = escape_display_text(match.get("title", "Untitled"))
                    authors = escape_display_text(match.get("authors", "Unknown author"))
                    badge_html = render_book_badges(soul, themes)
                    dna_html = render_book_dna(soul, description=description, categories=themes)
                    
                    # Soul Match bar color
                    if soul_match >= 75:
                        bar_color = "linear-gradient(90deg,#34d399,#6ee7b7)"
                    elif soul_match >= 55:
                        bar_color = "linear-gradient(90deg,#f59e0b,#fcd34d)"
                    else:
                        bar_color = "linear-gradient(90deg,#a78bfa,#f472b6)"
                        
                    soul_bar_html = (
                        '<div class="soul-match-wrap">'
                        '<span class="soul-match-label">Soul Match</span>'
                        '<div class="soul-match-bar-bg">'
                        f'<div class="soul-match-bar-fill" style="width:{soul_match}%;background:{bar_color};"></div>'
                        '</div>'
                        f'<span class="soul-match-pct">{soul_match}%</span>'
                        '</div>'
                    )
                    
                    desc_excerpt = smart_truncate(clean_display_text(description), max_length=280, complete_sentences=True)
                    desc_html = escape_display_text(desc_excerpt)
                    
                    col_cover, col_info = st.columns([1, 4.2], gap="large")
                    
                    with col_cover:
                        if match.get("cover_image"):
                            st.image(match["cover_image"], use_container_width=True)
                        else:
                            st.markdown('<div class="no-cover" style="width: 100%; aspect-ratio: 2/3; background: var(--card); border: 1px solid var(--border); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 2rem;">📖</div>', unsafe_allow_html=True)
                            
                    with col_info:
                        fallback_indicator = ""
                        if soul.get("is_fallback"):
                            fallback_indicator = '<span style="color:#f59e0b;font-size:0.7rem;margin-left:auto;background:rgba(245,158,11,0.1);padding:2px 8px;border-radius:4px;border:1px solid rgba(245,158,11,0.2);display:inline-flex;align-items:center;gap:4px;font-weight:600;">⚠️ Fallback Analysis</span>'
                            
                        st.markdown(textwrap.dedent(f"""
                        <div class="recs-card-horizontal">
                          <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;width:100%;">
                            <span class="rank-num">{index}</span>
                            <span style="font-family:\'Playfair Display\',serif;font-size:1.3rem;font-weight:700;color:#f1f5f9;">{title}</span>
                            {fallback_indicator}
                          </div>
                          <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:4px;">by {authors}</div>
                          
                          {soul_bar_html}
                          {badge_html}
                          {dna_html}
                          {f'<div class="book-desc" style="font-size: 0.85rem; color: var(--text-muted); border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px; line-height: 1.6;">{desc_html}</div>' if desc_html else ''}
                        </div>
                        """), unsafe_allow_html=True)
                        
                        # Favorite Toggle & Reasons Panel
                        col_fav_btn, col_blank = st.columns([1, 5])
                        with col_fav_btn:
                            is_fav = title in st.session_state["favorites"]
                            fav_lbl = "❤️ Favorite" if is_fav else "🖤 Favorite"
                            if st.button(fav_lbl, key=f"fav_rec_{index}_{title}"):
                                if is_fav:
                                    st.session_state["favorites"].remove(title)
                                else:
                                    st.session_state["favorites"].append(title)
                                st.rerun()
                                
                        if match_reasons:
                            reasons_html = "".join(
                                f'<div style="padding:3px 0;font-size:0.85rem;color:#c4b5fd;">'
                                f'• {escape_display_text(r)}</div>' for r in match_reasons
                            )
                            st.markdown(
                                f'<div class="match-reason">'
                                f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;'
                                f'text-transform:uppercase;color:#a78bfa;margin-bottom:6px;">'
                                f'✨ Why BookSoul Picked This</div>'
                                f'{reasons_html}</div>',
                                unsafe_allow_html=True
                            )
                    st.markdown("<hr style='border: none; border-top: 1px solid var(--border); margin: 2rem 0;'>", unsafe_allow_html=True)
            else:
                st.warning("No matches found. Try a different query — the internet search will fetch new books automatically.")

    # ── VIEW: SEARCH ────────────────────────────────────────
    elif active_tab == "Search":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 20px;">🔍 Search Library & Database</h2>', unsafe_allow_html=True)
        
        search_query = st.text_input("Enter book title, author, or keyword:", placeholder="e.g. Sarah J. Maas, Fourth Wing, Magic...")
        
        if search_query.strip():
            with st.spinner("Searching library database..."):
                results = collection.get(include=["metadatas"])
                
            if results and results.get("metadatas"):
                matches = []
                query_lower = search_query.lower().strip()
                
                for book_id, metadata in zip(results["ids"], results["metadatas"]):
                    title = metadata.get("title", "").lower()
                    authors = metadata.get("authors", "").lower()
                    description = metadata.get("description", "").lower()
                    
                    if query_lower in title or query_lower in authors or query_lower in description:
                        try:
                            soul = json.loads(metadata.get("soul_json_str", "{}"))
                        except Exception:
                            soul = {}
                        matches.append({
                            "id": book_id,
                            "title": metadata.get("title", "Untitled"),
                            "authors": metadata.get("authors", "Unknown"),
                            "cover_image": metadata.get("cover_image", ""),
                            "description": metadata.get("description", ""),
                            "soul": soul
                        })
                        
                if matches:
                    st.markdown(f"Found **{len(matches)}** matching books in your library database:")
                    
                    grid_cols = st.columns(3)
                    for idx, match in enumerate(matches):
                        col_idx = idx % 3
                        with grid_cols[col_idx]:
                            is_fav = match["title"] in st.session_state["favorites"]
                            fav_icon = "❤️" if is_fav else "🖤"
                            
                            cover_html = f'<img src="{match["cover_image"]}" class="cover-img-custom">' if match["cover_image"] else '<div style="width:100%; aspect-ratio:2/3; background:var(--card); display:flex; align-items:center; justify-content:center; font-size:2rem; border-radius:10px;">📖</div>'
                            
                            st.markdown(f"""
                            <div class="book-card-custom" style="margin-bottom: 15px;">
                              <div class="cover-wrap-custom">
                                {cover_html}
                              </div>
                              <div class="book-title-custom">{match["title"]}</div>
                              <div class="book-author-custom">by {match["authors"]}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_fav, c_btn = st.columns([1, 4])
                            with c_fav:
                                if st.button(fav_icon, key=f"fav_search_{match['id']}"):
                                    if is_fav:
                                        st.session_state["favorites"].remove(match["title"])
                                    else:
                                        st.session_state["favorites"].append(match["title"])
                                    st.rerun()
                            with c_btn:
                                if st.button("Details", key=f"details_search_{match['id']}", use_container_width=True):
                                    navigate_to("Recommendations", query=match["title"])
                else:
                    st.warning("No matches found in your local vector library. Try querying 'Recommendations' to search Google Books & the wider internet!")
            else:
                st.warning("Local library is currently empty. Go to the 'My Shelf' tab to manually index books into your database!")

    # ── VIEW: COMPARE ────────────────────────────────────────
    elif active_tab == "Compare":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 5px;">⚖️ Compare Books side-by-side</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">Analyze and compare the narrative DNA and pacing profiles of two books.</p>', unsafe_allow_html=True)
        
        col_b1, col_vs, col_b2 = st.columns([5, 1, 5])
        with col_b1:
            cmp_q1 = st.text_input("book1_query", label_visibility="collapsed", placeholder="Book 1 — e.g. Harry Potter", key="cmp_input1")
        with col_vs:
            st.markdown('<div style="text-align:center;padding-top:8px;font-size:1.3rem;font-weight:700;color:var(--accent-purple);">VS</div>', unsafe_allow_html=True)
        with col_b2:
            cmp_q2 = st.text_input("book2_query", label_visibility="collapsed", placeholder="Book 2 — e.g. Percy Jackson", key="cmp_input2")
            
        cmp_clicked = st.button("⚖️ Compare Now", key="cmp_btn")
        
        if cmp_clicked:
            if not cmp_q1.strip() or not cmp_q2.strip():
                st.warning("Please enter both book titles to compare.")
            else:
                with st.spinner("📚 Fetching books and analysing literary DNA..."):
                    result = compare_books(cmp_q1.strip(), cmp_q2.strip())
                    
                if "error" in result:
                    st.error(result["error"])
                else:
                    b1   = result["book1"]
                    b2   = result["book2"]
                    soul1 = result["soul1"]
                    soul2 = result["soul2"]
                    scores = result["scores"]
                    summary = result["summary"]
                    
                    hdr1, hdr2 = st.columns(2, gap="large")
                    for hdr_col, book, soul in [(hdr1, b1, soul1), (hdr2, b2, soul2)]:
                        with hdr_col:
                            cover_url = escape_display_text(book.get("cover_image", ""))
                            cover_html = f'<img src="{cover_url}" style="width:90px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.5);margin-bottom:10px;">' if cover_url else '<div class="no-cover" style="width:90px;height:135px;font-size:2rem;background:var(--card);display:flex;align-items:center;justify-content:center;border-radius:8px;">📖</div>'
                            authors_str = escape_display_text(book.get("authors", []), "Unknown")
                            fallback_html = ""
                            if soul.get("is_fallback"):
                                fallback_html = '<div style="color:#f59e0b;font-size:0.75rem;margin-bottom:8px;font-weight:600;">⚠️ Fallback Heuristic Analysis</div>'
                            st.markdown(f"""
                            <div class="book-card-custom" style="text-align:center; padding: 24px;">
                              <div style="display:flex;justify-content:center;margin-bottom:8px;">{cover_html}</div>
                              <div class="book-title-custom" style="font-size: 1.3rem;">{escape_display_text(book.get('title', 'Untitled'))}</div>
                              <div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:10px;">by {authors_str}</div>
                              {fallback_html}
                              <div style="display:flex;justify-content:center;gap:4px;flex-wrap:wrap;">
                                {render_badge(soul.get('reader_vibe', 'N/A'), 'vibe', '🧬')}
                                {render_badge(soul.get('writing_style', 'N/A'), 'style', '✍️')}
                                {render_badge(soul.get('emotional_tone', 'N/A'), 'trope', '🎭')}
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    st.markdown("<hr style='border: none; border-top: 1px solid var(--border); margin: 2rem 0;'>", unsafe_allow_html=True)
                    st.markdown('<p style="font-family:\'Playfair Display\',serif; text-align:center; font-size:1.5rem; font-weight:700; margin-bottom:20px;">Literary DNA Comparison</p>', unsafe_allow_html=True)
                    
                    for dim_score in scores:
                        name   = dim_score["name"]
                        icon   = dim_score["icon"]
                        s1     = dim_score["score1"]
                        s2     = dim_score["score2"]
                        d_type = dim_score["type"]
                        
                        def render_pips(score, pip_type, align="left"):
                            if pip_type == "pepper":
                                filled = "🌶️" * score
                                empty  = "<span style='opacity:0.25'>🌶️</span>" * (5 - score)
                            else:
                                filled = "⭐" * score
                                empty  = "<span style='opacity:0.25'>⭐</span>" * (5 - score)
                            if align == "right":
                                return empty + filled
                            return filled + empty
                            
                        win1_style = "color:#a78bfa;font-weight:700" if s1 > s2 else "color:#94a3b8"
                        win2_style = "color:#a78bfa;font-weight:700" if s2 > s1 else "color:#94a3b8"
                        
                        row_l, row_c, row_r = st.columns([4, 3, 4])
                        with row_l:
                            st.markdown(f'<div style="text-align:right;padding:6px 0;{win1_style}">{render_pips(s1, d_type, "right")}&nbsp;&nbsp;<strong>{s1}/5</strong></div>', unsafe_allow_html=True)
                        with row_c:
                            st.markdown(f'<div style="text-align:center;padding:6px 0;font-weight:600;">{icon} {name}</div>', unsafe_allow_html=True)
                        with row_r:
                            st.markdown(f'<div style="text-align:left;padding:6px 0;{win2_style}"><strong>{s2}/5</strong>&nbsp;&nbsp;{render_pips(s2, d_type)}</div>', unsafe_allow_html=True)
                            
                    st.markdown("<hr style='border: none; border-top: 1px solid var(--border); margin: 2rem 0;'>", unsafe_allow_html=True)
                    wins1 = summary["wins1"]
                    wins2 = summary["wins2"]
                    
                    v_col1, v_col2, v_col3 = st.columns([3, 4, 3])
                    with v_col1:
                        st.markdown(f"""
                        <div class="book-card-custom" style="text-align:center; padding: 20px;">
                          <div style="font-size:2.2rem;font-weight:700;color:var(--accent-purple);">{wins1}</div>
                          <div style="color:var(--text-muted);font-size:0.82rem;">categories won</div>
                          <div style="font-size:0.85rem;margin-top:6px;font-weight:600;">{b1["title"][:25]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with v_col2:
                        st.markdown(f"""
                        <div class="book-card-custom" style="text-align:center; padding: 20px;">
                          <div style="font-size:1.05rem;line-height:1.6;color:var(--text-primary);">{summary["verdict"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with v_col3:
                        st.markdown(f"""
                        <div class="book-card-custom" style="text-align:center; padding: 20px;">
                          <div style="font-size:2.2rem;font-weight:700;color:#f472b6;">{wins2}</div>
                          <div style="color:var(--text-muted);font-size:0.82rem;">categories won</div>
                          <div style="font-size:0.85rem;margin-top:6px;font-weight:600;">{b2["title"][:25]}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # ── VIEW: MY SHELF ───────────────────────────────────────
    elif active_tab == "Shelf":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 20px;">📚 My Shelf & Database</h2>', unsafe_allow_html=True)
        
        shelf_tabs = st.tabs(["📂 Library Collection", "⊕ Index New Book"])
        
        with shelf_tabs[0]:
            # Display all books in ChromaDB
            results = collection.get(include=["metadatas"])
            if results and results.get("metadatas"):
                st.markdown(f"Currently managing **{len(results['metadatas'])}** indexed books in your local vector database:")
                
                grid_cols = st.columns(3)
                for idx, (book_id, metadata) in enumerate(zip(results["ids"], results["metadatas"])):
                    col_idx = idx % 3
                    title = metadata.get("title", "Untitled")
                    authors = metadata.get("authors", "Unknown")
                    cover = metadata.get("cover_image", "")
                    
                    with grid_cols[col_idx]:
                        cover_html = f'<img src="{cover}" class="cover-img-custom">' if cover else '<div style="width:100%; aspect-ratio:2/3; background:var(--card); display:flex; align-items:center; justify-content:center; font-size:2rem; border-radius:10px;">📖</div>'
                        st.markdown(f"""
                        <div class="book-card-custom" style="margin-bottom: 15px;">
                          <div class="cover-wrap-custom">
                            {cover_html}
                          </div>
                          <div class="book-title-custom">{title}</div>
                          <div class="book-author-custom">by {authors}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_del, col_rec = st.columns(2)
                        with col_del:
                            if st.button("🗑️ Delete Book", key=f"del_shelf_{book_id}", use_container_width=True):
                                collection.delete(ids=[book_id])
                                st.success(f"Deleted '{title}' from DB.")
                                st.rerun()
                        with col_rec:
                            if st.button("🔮 Recommend", key=f"rec_shelf_{book_id}", use_container_width=True):
                                navigate_to("Recommendations", query=title)
            else:
                st.warning("Your vector library database is currently empty. Use the 'Index New Book' tab to index your first book!")
                
        with shelf_tabs[1]:
            st.markdown('<p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px;">Fetch a book synposis from Google Books and use AI to index its narrative DNA into ChromaDB.</p>', unsafe_allow_html=True)
            
            search_query = st.text_input("Search Google Books to Index:", placeholder="e.g. Wild Love by Elsie Silver  ·  Atomic Habits by James Clear", key="ingest_input")
            
            if st.button("📖 Fetch from Google Books", key="fetch_btn") and search_query:
                with st.spinner("Fetching from Google Books..."):
                    book = fetch_book_info(search_query)
                    if book:
                        is_valid, score, reason = validate_book(book)
                        if not is_valid:
                            st.error(f"⚠️ **Rejected by Librarian:** {reason}")
                        else:
                            st.session_state["fetched_book"] = book
                            st.session_state["fetched_book_score"] = score
                            for _k in ("current_soul", "current_book"):
                                if _k in st.session_state:
                                    del st.session_state[_k]
                    else:
                        st.error("No book found for that query. Try including the author name.")
                        
            if "fetched_book" in st.session_state:
                book = st.session_state["fetched_book"]
                fetched_cover = escape_display_text(book.get("cover_image", ""))
                fetched_description = clean_display_text(book.get("description", ""))
                fetched_description = smart_truncate(fetched_description, max_length=400, complete_sentences=True)
                st.markdown(f"""
                <div class="book-card-custom" style="margin-top:1.5rem; padding: 20px;">
                  <div style="display:flex;gap:1.5rem;align-items:flex-start; flex-wrap:wrap;">
                    <div style="flex-shrink:0; width: 110px;">
                      {"<img src='" + fetched_cover + "' style='width:100%; border-radius:8px; box-shadow:0 4px 20px rgba(0,0,0,0.5);'>" if fetched_cover else '<div style="width:100%; aspect-ratio:2/3; background:var(--card); display:flex; align-items:center; justify-content:center;">No Cover</div>'}
                    </div>
                    <div style="flex: 1; min-width: 250px;">
                      <div class="book-title-custom" style="font-size: 1.4rem;">{clean_display_text(book.get('title', 'Untitled'))}</div>
                      <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:10px;">by {clean_display_text(book.get("authors", []))}</div>
                      <div style="border-bottom:1px solid var(--border); padding:6px 0; font-size:0.85rem;"><span style="color:var(--text-muted); font-weight:500;">Published:</span> {clean_display_text(book.get("published_year", ""))}</div>
                      <div style="border-bottom:1px solid var(--border); padding:6px 0; font-size:0.85rem;"><span style="color:var(--text-muted); font-weight:500;">Categories:</span> {normalize_categories(book.get("categories", []))}</div>
                    </div>
                  </div>
                  <div style="margin-top:1.2rem; color:var(--text-muted); font-size:0.88rem; line-height:1.6;">{clean_display_text(fetched_description)}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔮 Generate BookSoul via Gemini", key="soul_btn"):
                    with st.spinner("Gemini is reading between the lines..."):
                        soul_json = generate_booksoul(book["title"], book.get("description", ""), ", ".join(book.get("categories", [])))
                    if "error" in soul_json:
                        st.error(soul_json["error"])
                    else:
                        st.session_state["current_soul"] = soul_json
                        st.session_state["current_book"] = book
                        
            if "current_soul" in st.session_state:
                soul = st.session_state["current_soul"]
                book = st.session_state.get("current_book", {})
                themes_display = soul.get("themes", [])
                tropes_display = soul.get("tropes", [])
                dna_html = render_book_dna(soul, description=book.get("description", ""), categories=book.get("categories", themes_display))
                
                header_text = "⚠️ Rule-Based Analysis (Quota Fallback)" if soul.get("is_fallback") else "🔮 BookSoul Generated"
                header_color = "#f59e0b" if soul.get("is_fallback") else "#a78bfa"
                
                st.markdown(f"""
                <div class="book-card-custom" style="margin-top:1.5rem; padding: 20px;">
                  <div style="font-family:\'Playfair Display\',serif;font-size:1.15rem;font-weight:700;margin-bottom:12px;color:{header_color};">{header_text}</div>
                  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;">
                    {render_badge('Vibe: ' + clean_display_text(soul.get('reader_vibe', 'N/A')), 'vibe')}
                    {render_badge('Style: ' + clean_display_text(soul.get('writing_style', 'N/A')), 'style')}
                    {render_badge('Tone: ' + clean_display_text(soul.get('emotional_tone', 'N/A')), 'trope')}
                    {render_badge('Pacing: ' + clean_display_text(soul.get('pacing', 'N/A')), 'trope')}
                  </div>
                  <div style="margin-bottom:8px;">{render_badge_group(tropes_display, 'trope')}</div>
                  <div>{render_badge_group(themes_display, 'vibe')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(dna_html, unsafe_allow_html=True)
                
                book_title = st.session_state["current_book"]["title"]
                book_id = "".join(e for e in book_title if e.isalnum()).lower()
                
                if st.button("💾 Save to ChromaDB", key="save_btn"):
                    with st.spinner("Embedding narrative text and indexing into ChromaDB..."):
                        success = store_book_vector(
                            book_id=book_id,
                            book_title=book_title,
                            book_metadata=st.session_state["current_book"],
                            soul_json=st.session_state["current_soul"],
                            quality_score=st.session_state.get("fetched_book_score", 0)
                        )
                    if success:
                        st.success(f"✅ '{book_title}' is now in your vector library!")
                        with st.spinner("Verifying DB record..."):
                            retrieved = retrieve_book_vector(book_id)
                        if retrieved:
                            with st.expander("View stored vector payload"):
                                st.code(retrieved["document"], language="text")
                    else:
                        st.error("Failed to write to ChromaDB.")

    # ── VIEW: MOOD JOURNAL ───────────────────────────────────
    elif active_tab == "Mood":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 10px;">📝 My Mood Journal</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">Track your reading mood logs and get matching BookSoul recommendation shortlists.</p>', unsafe_allow_html=True)
        
        with st.form("mood_form"):
            mood_input = st.text_area("How are you feeling today? What kind of vibe are you looking for in a book?", placeholder="e.g. Tired and stressed after exams. I want a cozy fantasy like found family that is extremely comforting and slow-paced.")
            log_btn = st.form_submit_button("📝 Log Mood & Recommend Books")
            
            if log_btn and mood_input.strip():
                import datetime
                log_entry = {
                    "date": datetime.datetime.now().strftime("%d %B %Y - %I:%M %p"),
                    "mood": mood_input.strip()
                }
                st.session_state["mood_logs"].insert(0, log_entry)
                navigate_to("Recommendations", query=mood_input.strip())
                
        if st.session_state["mood_logs"]:
            st.markdown("<h4 style='font-family: \"Playfair Display\", serif; margin-top: 30px; margin-bottom: 15px;'>Past Mood Entries</h4>", unsafe_allow_html=True)
            for idx, entry in enumerate(st.session_state["mood_logs"]):
                st.markdown(f"""
                <div class="book-card-custom" style="margin-bottom: 15px; padding: 20px;">
                  <div style="font-size: 0.75rem; color: var(--accent-purple); font-weight: 600; margin-bottom: 8px;">{entry['date']}</div>
                  <div style="font-size: 0.92rem; line-height: 1.6; color: var(--text-primary); margin-bottom: 12px;">"{entry['mood']}"</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔮 Match Books", key=f"match_mood_{idx}"):
                    navigate_to("Recommendations", query=entry["mood"])
        else:
            st.info("No logs in your mood journal yet. Write down how you are feeling above to log and find matches!")

    # ── VIEW: FAVORITES ──────────────────────────────────────
    elif active_tab == "Favorites":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 10px;">❤️ My Favorites</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">Your personal shortlist of favorited book souls.</p>', unsafe_allow_html=True)
        
        if st.session_state["favorites"]:
            # Query the database for the favorited book titles
            results = collection.get(include=["metadatas"])
            fav_matches = []
            if results and results.get("metadatas"):
                for book_id, metadata in zip(results["ids"], results["metadatas"]):
                    title = metadata.get("title", "")
                    if title in st.session_state["favorites"]:
                        try:
                            soul = json.loads(metadata.get("soul_json_str", "{}"))
                        except Exception:
                            soul = {}
                        fav_matches.append({
                            "id": book_id,
                            "title": title,
                            "authors": metadata.get("authors", "Unknown"),
                            "cover_image": metadata.get("cover_image", ""),
                            "description": metadata.get("description", ""),
                            "soul": soul
                        })
                        
            if fav_matches:
                grid_cols = st.columns(3)
                for idx, match in enumerate(fav_matches):
                    col_idx = idx % 3
                    with grid_cols[col_idx]:
                        cover_html = f'<img src="{match["cover_image"]}" class="cover-img-custom">' if match["cover_image"] else '<div style="width:100%; aspect-ratio:2/3; background:var(--card); display:flex; align-items:center; justify-content:center; font-size:2rem; border-radius:10px;">📖</div>'
                        st.markdown(f"""
                        <div class="book-card-custom" style="margin-bottom: 15px;">
                          <div class="cover-wrap-custom">
                            {cover_html}
                          </div>
                          <div class="book-title-custom">{match["title"]}</div>
                          <div class="book-author-custom">by {match["authors"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_unfav, col_rec = st.columns(2)
                        with col_unfav:
                            if st.button("💔 Remove", key=f"unfav_{match['id']}", use_container_width=True):
                                st.session_state["favorites"].remove(match["title"])
                                st.success(f"Removed '{match['title']}' from favorites.")
                                st.rerun()
                        with col_rec:
                            if st.button("🔮 Recommendations", key=f"rec_fav_{match['id']}", use_container_width=True):
                                navigate_to("Recommendations", query=match["title"])
            else:
                st.warning("None of your favorited books are currently stored in your vector database collection.")
        else:
            st.info("You haven't favorited any books yet. Click the heart ❤️ icon on recommendations cards or search matches to build your list!")

    # ── VIEW: HISTORY ────────────────────────────────────────
    elif active_tab == "History":
        st.markdown('<h2 style="font-family: \'Playfair Display\', serif; font-size: 2rem; font-weight: 700; margin-bottom: 10px;">🕒 Search History</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">Review and quickly rerun your previous mood search queries.</p>', unsafe_allow_html=True)
        
        if st.session_state["search_history"]:
            for idx, q in enumerate(st.session_state["search_history"]):
                st.markdown(f"""
                <div class="book-card-custom" style="margin-bottom: 15px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <span style="font-size: 0.82rem; color: var(--accent-purple); font-weight: 600; margin-right: 15px;">Query #{idx+1}</span>
                    <span style="font-size: 0.95rem; font-weight: 500;">"{escape_display_text(q)}"</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_run, col_del = st.columns([1, 5])
                with col_run:
                    if st.button("🔮 Run", key=f"run_hist_{idx}"):
                        navigate_to("Recommendations", query=q)
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_hist_{idx}"):
                        st.session_state["search_history"].remove(q)
                        st.success("Deleted from history.")
                        st.rerun()
        else:
            st.info("No queries logged in your search history yet. Rerun some recommendations to populate it!")
