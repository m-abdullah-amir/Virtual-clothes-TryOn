# NextGen Smart Virtual Try-On System — Master Project Specification

**Read this entire document before writing any code. If anything is unclear, missing, or you need a file/credential/asset that hasn't been provided, STOP and ask the user directly instead of guessing or inventing a placeholder silently. Work in the phases listed at the end of this document, committing to git after each phase, rather than attempting everything at once.**

---

## 1. WHAT THIS PROJECT IS

NextGen Smart Virtual Try-On is a web application that lets a user upload a photo of themselves and a photo of a garment, and generates a realistic image showing them wearing that garment. It solves the "visualization gap" in online clothing shopping — customers can't tell how something will actually look on their own body before buying it.

This is a portfolio project built by a BSCS student to demonstrate applied AI/full-stack engineering skills. It must be a real, working, deployed product — not a mockup — since it will be linked on the developer's LinkedIn/resume for recruiters to try.

---

## 2. CORE FEATURES

### Must-have (build these first, in this order of priority):
1. **Photo upload** — user uploads a full-body photo of themselves
2. **Garment upload** — user uploads a photo of a single clothing item
3. **AI-generated try-on result** — the system generates a realistic composite image
4. **Download result** — user can save the generated image
5. **Try another** — user can restart the flow without losing their uploaded self-photo (only needs to re-upload/change the garment)

### Enhanced features (build after the must-haves work end-to-end):
6. **Multi-garment / layered outfits** — instead of uploading one garment, the user can optionally upload a top (shirt/jacket) AND a bottom (pants/skirt) separately, and the system composites both onto their photo as a complete outfit.
7. **Tuck-in toggle** — when a top garment is included, show a toggle switch labeled "Tuck in shirt." This is an EXPERIMENTAL feature — see section 7.5 for honest implementation guidance. Do not claim this works perfectly; implement it as a best-effort attempt and clearly document its actual reliability once tested.
8. **Stage-aware processing feedback** — instead of a generic "Loading...", show the user which pipeline stage is currently running (e.g., "Removing background...", "Analyzing your pose...", "Generating your look..."). This is realistic to implement since we know the exact pipeline stages, and it meaningfully improves perceived quality/professionalism.
9. **Proper error states** — do not build only the happy path. Handle and clearly display: upload failures (wrong file type, file too large), no-person-detected in the self-photo, generation failures/timeouts, and backend-unreachable errors. Each should show a clear, friendly message and a way to retry — not a blank screen or a raw error stack.

### Explicitly out of scope for now (do not build unless asked):
- User accounts / login
- Payment or e-commerce integration
- Saved history of past try-ons (may be added later as a stretch goal using a small local JSON or SQLite file — do not build this yet)

---

## 3. TECH STACK (fixed — do not substitute any of these without asking first)

**Frontend:**
- Next.js (App Router)
- Tailwind CSS
- Deployed to Vercel (account already connected to GitHub)

**Backend / AI inference:**
- Hosted on **Modal** (modal.com) as Python serverless functions — NOT Hugging Face Spaces (this was the original plan but was changed; do not reference or set up anything on Hugging Face Spaces for hosting)
- Modal CLI is already installed and authenticated on this machine. Token is cached at `C:\Users\BN Computers\.modal.toml`. Do not ask the user for a Modal API key — just use `modal` CLI commands directly and they will authenticate automatically.
- GPU usage: use `gpu="A10G"` in the Modal function decorator specifically for the CatVTON generation step. Background removal (rembg) and pose detection (MediaPipe) should run as CPU-only Modal functions to avoid unnecessary GPU cost — GPU time is the only meaningfully billed resource here.

**Hugging Face (limited role):**
- The HF CLI is already authenticated on this machine (`huggingface-cli login` already run). This is ONLY needed if CatVTON's model weights must be downloaded from a gated Hugging Face repository at runtime inside the Modal function. Hugging Face is NOT used for hosting or deployment in this project.

**AI pipeline components:**
- Garment background removal: `rembg` (Python package)
- Pose/body analysis: `mediapipe` (Google's MediaPipe Pose)
- Try-on generation: **CatVTON** — clone from `github.com/Zheng-Chong/CatVTON`. Adapt its inference logic to run as a Modal function rather than its default Gradio-on-HF-Spaces setup. Use their repo's inference code as the reference for correct model loading and generation calls, but restructure it to fit Modal's `@app.function()` pattern.

---

## 4. REPOSITORY & ENVIRONMENT (already set up — do not recreate)

- GitHub repo: `m-abdullah-amir/Virtual-clothes-TryOn` — this folder is already cloned and git-connected to it. Commit incrementally as features are completed. Do not make one giant commit at the end.
- Modal account: already created, authenticated, spend budget capped by the user in Modal's dashboard.
- Hugging Face account: already created, CLI authenticated.

If you need any additional credential, API key, or account that isn't listed above, STOP and ask the user — do not attempt to sign up for new services or generate placeholder keys.

---

## 5. DESIGN SYSTEM (apply exactly and consistently across all screens)

**Colors:**
- Background / Creme: `#EEE4DA`
- Secondary / Sand: `#D8C4AC`
- Accent / Dusty Pink: `#C8A49F`
- Primary / Burgundy: `#4D0E13` (headings, primary buttons, key accents)
- Success / Green: `#2FA76B` (used only for the Download button and "Ready" status indicators)
- Body text: `#6B6B6B`
- Muted / label text: `#A89A8C`

**Typography:**
- Headings: serif font, color `#4D0E13`, weight 600. An italic variant of the same serif font is used for secondary heading lines (see per-screen specs below).
- Body and UI text: clean sans-serif
- Small labels (e.g. "NEXTGEN", "Step 1 of 2"): uppercase, wide letter-spacing, 13–14px, muted color (`#A89A8C`)

**Shape and spacing:**
- Border-radius: 12px on cards, 4px on buttons (slightly rounded rectangles, not pill-shaped except the nav bar)
- Use a consistent 8px spacing grid throughout (8, 16, 24, 32, 48px gaps)

**Shared floating navigation (present on all 4 screens):**
- Pill-shaped container, white/cream background, horizontally centered near the bottom of the viewport, slightly floating above the page content
- 4 items: Home / Upload / Processing / Result
- Active item: solid `#4D0E13` background, `#EEE4DA` text
- Inactive items: transparent background, muted dark text
- Uppercase, wide letter-spacing, padding 12px 24px per item, 8px internal padding around the whole pill, fully rounded corners

**Page transitions:** fade-in + 20px upward slide on screen load, ~300ms ease-out, applied consistently on all 4 screens.

---

## 6. SCREEN-BY-SCREEN FRONTEND SPECIFICATION

### SCREEN 1: Landing Page (Hero)

Full-width section, two columns on desktop; stack vertically below 768px width.

**Left column (~40% width, vertically centered):**
1. "NEXTGEN" label — uppercase, wide letter-spacing, `#A89A8C`, 14px
2. Heading: "Virtual" (serif, `#4D0E13`, 64px, weight 600), then "Try-On" on the next line in the same serif font but italic
3. Thin horizontal divider, 60px wide, `#D8C4AC`, 24px margin top and bottom
4. Body text: "See any garment on yourself — before you buy. Powered by AI, made for fashion." — sans-serif, `#6B6B6B`, 18px, line-height 1.6, max-width 380px
5. Button: "TRY IT NOW" — solid `#4D0E13` background, `#EEE4DA` text, uppercase, wide letter-spacing, padding 16px 32px, 4px border-radius. Hover: background darkens slightly, scale to 1.02x, 200ms transition. Clicking navigates to the Upload screen.
6. Small text: "✦ AI-powered · Instant results" — 13px, `#A89A8C`, roughly 80px margin-top from the button

**Right column (~60% width):**
- A single hero image asset at `/public/images/hero-image.png`. If this file does not exist yet when you reach this step, use a correctly-sized placeholder with a note/comment in the code flagging that the real image needs to be added — do NOT generate or invent a substitute image yourself, and clearly tell the user this file is missing.
- Full-bleed to the right edge of the viewport, `object-fit: cover`

**Background:** `#EEE4DA` behind the left column; the image fills the right column flush against it, no visible gap or seam between them.

**Responsive:** below 768px, stack to a single column — image on top (reduced height, ~300px), text content below it, nav bar remains full-width at the bottom.

---

### SCREEN 2: Upload Screen

**Top bar:** "NEXTGEN" (top-left) and "Step 1 of 2" (top-right), same label styling as the hero screen.

**Heading:** "Upload Your Photos" — serif, `#4D0E13`, 48px, weight 600, 40px margin-top. Subtext below: "One photo of you, one of the garment — we do the rest." — sans-serif, `#6B6B6B`, 18px, 12px margin-top.

**Mode selector (new — build this before the upload cards):**
A small segmented toggle/tab control, centered, below the subtext, above the upload cards:
- "Single Garment" (default selected)
- "Complete Outfit (Top + Bottom)"

Styled consistently with the design system — active segment gets `#4D0E13` background with `#EEE4DA` text, inactive segment is transparent with muted text, both inside a pill-shaped container.

**Upload cards — behavior depends on the selected mode:**

*If "Single Garment" is selected (default):* show 2 cards side by side, exactly as follows.
*If "Complete Outfit" is selected:* show 3 cards — "Your Photo", "Top / Shirt Photo", "Bottom / Pants Photo" — adjust the grid to fit 3 equal-width cards instead of 2 (reduce individual card width proportionally, keep the same 24px gap).

Each card:
- Background `#F5EDE4`, border-radius 12px, min-height 480px (reduce proportionally if 3 cards are shown to avoid excessive page height — use your judgment to keep it visually balanced)
- Centered content: circular icon (64px diameter, 1px `#D8C4AC` border, transparent background, an image+plus icon inside colored `#C8A49F`), label below it (serif, `#4D0E13`, 24px, 20px margin-top — "Your Photo" / "Top / Shirt Photo" / "Bottom / Pants Photo" / "Garment Photo" depending on mode and card), "Click to upload" below that (sans-serif, `#A89A8C`, 15px, 8px margin-top)
- Hover state: card background darkens slightly, icon border deepens, 200ms transition
- Once an image is uploaded: replace the placeholder content with the actual uploaded image, `object-fit: cover`, filling the card, with a small "×" remove button in the top-right corner
- Must be real functional file upload inputs, accepting standard image formats (jpg, png, webp). Validate file type and a reasonable max size (e.g. 10MB) client-side, and show a clear error message if validation fails (see section 2, error states).

**Tuck-in toggle (only shown when a top/shirt garment is present — i.e. "Single Garment" mode with a shirt-type garment uploaded, OR "Complete Outfit" mode):**
- A labeled toggle switch: "Tuck in shirt" with an on/off switch styled in the design system's colors (`#4D0E13` when on, `#D8C4AC` track when off)
- Positioned below the upload cards, above the Generate button
- See section 7.5 for backend implementation guidance — this is experimental, build the UI regardless but be honest with the user about how well the actual generation respects this setting once you test it

**Generate button:** "GENERATE TRY-ON", centered, 40px margin-top below the cards/toggle.
- Disabled state (required uploads for the current mode not yet filled): `#C8A49F` at 50% opacity, white text at 70% opacity, not clickable
- Active state (all required uploads present): solid `#4D0E13` background, `#EEE4DA` text, fully clickable, hover scale 1.02x
- Padding 16px 48px, 4px border-radius, uppercase, wide letter-spacing
- On click: send the uploaded image(s) + mode + tuck-in preference to the backend, then navigate to the Processing screen

---

### SCREEN 3: Processing Screen

Full viewport height, all content centered (vertical and horizontal). Background: solid `#EEE4DA`.

**Loading indicator:** circular element, ~120px diameter. Outer faint ring (`#D8C4AC` at low opacity, decorative), inner partial arc (roughly 90–120 degrees of the circle, `#4D0E13`, 3px stroke width), continuously rotating (~2 seconds per rotation, smooth ease-in-out or linear). Small solid dot in `#4D0E13` centered inside.

**Stage-aware text (build this — see feature #8 in section 2):** below the spinner, show dynamically updating text reflecting the actual current pipeline stage, in this sequence:
1. "Removing background..." (during rembg step)
2. "Analyzing your pose..." (during MediaPipe step)
3. "Generating your look..." (during CatVTON generation — this is the longest step, keep this text shown until generation completes)

Text styling: serif, italic, `#4D0E13`, 32px. Below it, smaller supporting text `#A89A8C`, 15px (e.g. "This may take a moment").

**Top loading bar:** thin horizontal progress indicator fixed to the very top of the viewport, full width, ~3px height, animated to suggest ongoing activity — separate visual element from the circular spinner, a subtle page-level loading cue.

**Error handling:** if the backend returns an error or times out, replace this screen's content with a clear error message and a "Try Again" button that returns the user to the Upload screen without losing their uploaded images if possible.

---

### SCREEN 4: Result Screen

**Top bar:** "NEXTGEN" (top-left), and a status indicator top-right — "✦ Ready" in `#2FA76B` (green) with a small sparkle/star icon, once the result has loaded.

**Background:** a soft, blurred abstract background blending `#C8A49F` and `#EEE4DA` tones — subtle and out of focus, sitting behind all content at low visual weight. Not a photograph.

**Layout — two columns:**

*Left column (~45% width):* the result image.
- Portrait aspect ratio container (roughly 3:4), border-radius 8px, subtle shadow, with a soft secondary offset shadow/edge behind it for a slightly layered look
- Displays the actual generated try-on image returned by the backend

*Right column (~45% width, vertically centered relative to the image):*
- "YOUR RESULT" — small label, uppercase, wide letter-spacing, `#C8A49F`, 13px
- "How it" (serif, `#4D0E13`, 44px, weight 600), then "looks on you" on the next line, same style but italic
- Thin horizontal divider, 60px wide, `#D8C4AC`, 20px vertical margin
- Body text: "AI has composed the outfit on your silhouette. Save it or start fresh." — sans-serif, `#6B6B6B`, 16px
- **"DOWNLOAD" button** — solid `#2FA76B` background, white text, download icon on the left, full-width of this column, padding 16px, 4px border-radius, 32px margin-top, uppercase, wide letter-spacing. Must trigger an actual file download of the generated image, not just open it in a new tab.
- **"TRY ANOTHER" button** — transparent background, 1px `#4D0E13` border, `#4D0E13` text, refresh icon on the left, same sizing as Download button, 12px margin-top. Clicking this should return to the Upload screen, ideally preserving the user's self-photo (so they only need to change the garment) — see feature #5 in section 2.

---

## 7. BACKEND PIPELINE — DETAILED IMPLEMENTATION GUIDANCE

### 7.1 Overall structure
Build this as a set of Modal functions in a single Python app (e.g. `modal_app.py`), deployed via `modal deploy`. Expose one web endpoint the frontend can call with the uploaded images and options, which internally runs the full pipeline and returns the final image.

### 7.2 Stage 1 — Garment background removal (rembg)
- Runs on CPU
- Takes the garment image(s), strips the background, outputs a clean transparent-background PNG
- Skip this stage for the "Your Photo" (self) image — only garment images need background removal

### 7.3 Stage 2 — Pose/body analysis (MediaPipe)
- Runs on CPU
- Analyzes the self-photo to extract body landmarks needed by CatVTON for accurate garment placement

### 7.4 Stage 3 — Try-on generation (CatVTON on GPU)
- Runs on Modal with `gpu="A10G"`
- Adapt CatVTON's inference code (from their GitHub repo) into a Modal function
- For "Single Garment" mode: standard single-pass generation
- For "Complete Outfit" mode: run CatVTON twice in sequence — first pass generates the result with the top garment, then feed that output back in as the new "person" image for a second pass with the bottom garment. Document this clearly in code comments since it's a workaround, not a native CatVTON feature.

### 7.5 Tuck-in toggle — HONEST IMPLEMENTATION NOTE
CatVTON does not have a native, documented parameter for controlling whether a shirt appears tucked in or not. Do not assume this will work reliably. Implement it as a best-effort attempt using whichever of these is actually feasible once you inspect CatVTON's code:
- If CatVTON accepts any text/style conditioning input, append a descriptive hint (e.g. "tucked in" vs "untucked, loose fit") to that input
- If no such input exists, implement the toggle in the UI regardless (so the feature is visibly present for the portfolio), but clearly document in the code and to the user that it may not produce a visible or reliable difference in the output, since the underlying model wasn't trained with explicit tuck-in control
- Do not fabricate a fake visual effect (e.g. cropping/warping the image to fake a tuck) — that would be misleading. If it's not achievable through the model itself, be upfront about the limitation rather than faking it.

### 7.6 API contract (frontend ↔ backend)
Design the request format as:
```
POST to the Modal web endpoint with:
- person_image (file)
- mode ("single" | "complete_outfit")
- garment_image (file, required if mode = "single")
- top_image (file, required if mode = "complete_outfit")
- bottom_image (file, required if mode = "complete_outfit")
- tuck_in (boolean, optional)

Response:
- result_image (the generated image, or a URL to it)
- OR an error object with a clear message if something failed
```
Adjust field names as needed to fit Modal's actual web endpoint conventions, but keep this general shape so the frontend logic stays simple and predictable.

---

## 8. RULES FOR THE AGENT (read again before starting)

1. **Ask, don't guess.** If a required file, asset, credential, or piece of information isn't available in this document or the repo, stop and ask the user directly.
2. **Work in phases** (see section 9 below), committing to git after each phase completes and works, not all at once at the end.
3. **Do not hardcode any secrets** (API keys, tokens) directly in code files. Use environment variables / Modal secrets where credentials are needed.
4. **Be honest about limitations.** If something described in this spec (especially the tuck-in feature) doesn't work reliably once implemented and tested, say so clearly rather than presenting it as fully working.
5. **Test each pipeline stage independently before wiring them together**, so failures are easier to isolate.
6. **Keep the design system values (colors, fonts, spacing) consistent** — do not substitute similar-looking values; use the exact hex codes and measurements given.

---

## 9. BUILD ORDER (follow this sequence)

**Phase 1 — Backend foundation**
- Set up the Modal app skeleton, confirm `modal deploy` works with a simple "hello world" function first
- Implement Stage 1 (rembg) as a standalone Modal function, test it independently
- Implement Stage 2 (MediaPipe pose) as a standalone Modal function, test it independently

**Phase 2 — Core AI pipeline**
- Clone and adapt CatVTON into a Modal GPU function
- Get single-garment, single-pass generation working end-to-end (Stage 1 → 2 → 3), test with sample images
- Confirm the web endpoint works via a simple test request (e.g. curl or Postman) before building the frontend against it

**Phase 3 — Frontend skeleton**
- Set up the Next.js + Tailwind project structure
- Build Screen 1 (Landing/Hero) and Screen 2 (Upload) with the single-garment mode only, wired to the working backend endpoint from Phase 2
- Build Screen 3 (Processing) and Screen 4 (Results), confirming the full user flow works for single-garment mode

**Phase 4 — Enhanced features**
- Add "Complete Outfit" mode (frontend 3-card UI + backend two-pass generation logic)
- Add the tuck-in toggle (frontend UI + best-effort backend attempt, per section 7.5)
- Add stage-aware processing text (Screen 3 enhancement)
- Add proper error states across all screens

**Phase 5 — Polish and deploy**
- Apply the full design system precisely across all screens if not already exact
- Add the hero image asset (ask the user for this file if not already present)
- Deploy frontend to Vercel
- Final end-to-end test of the live deployed app

Do not skip ahead to later phases before earlier ones are working — confirm each phase functions correctly before proceeding.
