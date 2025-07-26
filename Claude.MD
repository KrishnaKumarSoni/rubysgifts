# Ruby's Gifts App

<!-- CLAUDE_PROMPT: You are a senior product engineer and full-stack developer specializing in intuitive UX for web apps using Flask, vanilla HTML/CSS/JS. Build a complete, production-ready web app based on the requirements, focusing on the enhanced chip-based input system for superior user experience. Reason step-by-step as a product engineer: 1. Analyze UX goals (e.g., make answering fun/efficient with suggestions, reduce typing friction via multi-select chips, enable discovery through search/icons). 2. Outline app structure with emphasis on JS-driven chip interactions. 3. Define extensive option lists (50+ per question) with Phosphor Icons mappings. 4. Implement backend for OpenAI. 5. Ensure responsive, accessible design. Output full codebase in separate markdown code blocks per file. Include setup, comments, dependencies. Use artifacts for UI previews (e.g., chip grid mockup). Think aloud concisely in response. -->

## Objective
Create "ruby's gifts" app with improved UX: Users get AI-powered gift ideas after answering questions. Enhance each question with a searchable, multi-select chip interface featuring "tons" (50+ per question) of suggestion chips, each with a Phosphor Icon for visual appeal. Chips aid quick selection; sync selections to a text input for editing/combining. Goal: Make input feel exploratory, fun, and efficient—reduce cognitive load by suggesting common/creative options, allow multi-select for nuanced answers, enable search for quick filtering, and permit custom typing. As a product engineer: This UX turns rote forms into an engaging "discovery" experience, boosting completion rates; chips with icons add delight and context (e.g., heart icon for romantic relationships); syncing to text input ensures flexibility (edit/add/remove) while preventing data silos; handle overflow with scrollable grids; prioritize mobile (touch-friendly chips); accessibility via keyboard nav/ARIA.


# Deployment
Vercel - via cli 
github - via CLi

## Requirements

### User Flow
- Landing: Simple welcome, start button.
- Questionnaire: One question per "page" (JS-toggled, smooth transitions). For each: Heading, searchable input to filter chips, grid of many chips (multi-select, toggle on click), synced text input (textarea for multi-line editing). Progress bar. Next/prev buttons. Submit on last.
- Results: 3 gift cards with ideas, starters, reactions. Retry for errors.

### Enhanced Question UX (Per Question)
- **Core Mechanic**: Below question text, show a search bar (input) that filters visible chips in real-time (case-insensitive, fuzzy match on chip text).
- **Chips**: Grid of 50+ options (generate extensive lists; examples below—expand creatively, e.g., via common phrases/personalities/items). Each chip: Rounded pill (orange accent when selected), Phosphor Icon (via CDN: https://unpkg.com/phosphor-icons), descriptive text. Multi-select: Click toggles selection (add visual state: bg-orange, check icon).
- **Sync with Text Input**: Textarea at top/bottom for final answer. On chip select: Append chip's text (comma-separated if multi) to textarea. On unselect: Remove that exact text segment. User can type/edit freely in textarea (chips don't override manual input, but sync selections additively). If user edits textarea, don't auto-deselect chips—treat as override for flexibility.
- **Searchable**: Filter chips dynamically; show "no matches" if empty. Infinite scroll or pagination if truly "too many" (aim for 100+ to feel abundant).
- **Multi-Select & Both**: Users can select multiple chips (appends all), type custom text, or mix (e.g., select chips then edit textarea).
- **Product Engineer Thoughts**: This creates a "suggestion engine" UX—chips spark ideas (e.g., for "hates," suggest phobias/items with icons); search reduces overwhelm; icons add emotional cues (e.g., skull for hates); textarea as "collector" ensures composability; handle edge cases like duplicate selections (prevent), long lists (virtual scrolling in JS), mobile tap (large chips).

### Questions with Example Chip Options (Expand to 50+ Each)
Generate full lists in code (e.g., JS arrays). Map icons logically (e.g., Phosphor: heart for positive, skull for negative). Examples (10-15 here; code should have 50+ varied/creative ones):
1. What do you call them? Chips: Common nicknames/pet names (e.g., "buddy" with user icon, "sweetheart" with heart, "bro" with handshake; expand to 100+ like diminutives from cultures/languages).
2. What's your relationship? Chips: Nuanced relations (e.g., "best friend" with star, "sibling" with users, "crush" with flame; expand: "work buddy," "ex-partner," "mentor," etc.).
3. What have you already gifted them? Chips: Gift ideas (e.g., "chocolate" with cake, "book" with book, "jewelry" with diamond; expand: gadgets, experiences, personalized items—100+ common gifts).
4. What will they absolutely hate? Chips: Dislikes (e.g., "spiders" with bug, "loud noises" with speaker, "cheap plastic" with trash; expand: foods, activities, tropes—phobias/allergies/materials).
5. What do they keep complaining about? Chips: Complaints (e.g., "traffic" with car, "work stress" with briefcase, "bad weather" with cloud; expand: daily annoyances, health, tech fails—100+ relatable gripes).
6. How would you complain about them to someone? Chips: Quirks (e.g., "always late" with clock, "too picky" with magnifying-glass, "loud chewer" with mouth; expand: personality flaws, habits—humorous/venting phrases).
7. What's your budget? Adapt to chips: Common ranges/items (e.g., "under 500₹" with coin, "luxury splurge" with money-bag; expand: specific amounts/categories— but keep slider for precision; sync selected ranges to textarea as "e.g., 500-1000₹").
8. Any other limitations? Chips: Constraints (e.g., "allergy-free" with shield, "eco-friendly" with leaf, "portable" with backpack; expand: size, theme, ethical—100+ filters).

For all: Textarea is required (except optional ones); validate non-empty on next.

### Design Style
- Bright social, orange primary (#FF6600).
- Chips: Large round (border-radius: 32px), hover effects, selected state.
- No shadows; lowercase text (CSS transform, except names).
- Fonts: Playfair Display Medium (headings), Plus Jakarta Sans (body).
- Icons: Only Phosphor (CDN; e.g., <i class="ph ph-heart"></i>).
- Responsive: Chip grid flex-wraps, searchable on mobile.

### Tech Stack
- Backend: Flask, OpenAI SDK (.env key).
- Frontend: Vanilla HTML/JS/CSS; JS for chip filtering/selection/sync, fetch to /generate_gifts.
- LLM: GPT-4o-mini; prompt with concatenated answers (include chip-selected texts).

## Code Style
- Modular: JS functions for chip rendering/filtering/sync.
- Accessible: ARIA for chips/search, keyboard toggle.
- Edge Cases: Duplicate chips, search typos (fuzzy), textarea overrides, high option count (performance via DOM efficiency).

## Bash Commands
- Run: `python app.py`
- Install: `pip install flask python-dotenv openai`

## Testing Instructions
- UX Focus: Test chip search/select/sync, mobile scrolling, idea generation quality.