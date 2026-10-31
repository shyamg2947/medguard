# MedGuard Design System

## 1. Philosophy & Brand Identity

The MedGuard design system is inspired by Apple's minimalist, typographic, and calm design language. It prioritizes clarity, generous whitespace, soft depth, and uncompromising accessibility for elderly patients and clinical reviewers.

### Legal & Ethical Brand Rules
- **Original Assets Only:** No Apple logos, copyrighted assets, trademarked typography files (SF Pro), or hardware replicas are used.
- **Open Standards:** The font stack utilizes the system font cascade with open-source fallbacks (`Inter`, `Noto Sans Devanagari`, `Noto Sans Kannada`).
- **Original Symbol:** MedGuard's icon is an original medical shield with an integrated rhythmic pulse line.
- **Strictly No Emoji:** Per Section 7.16, interface cues use clean SVG line icons from the open-source Lucide library. Never rely on emoji in the UI.

---

## 2. Design Tokens

Defined in `frontend/src/styles/tokens.css`:

```css
:root {
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Inter",
          "Noto Sans", "Noto Sans Devanagari", "Noto Sans Kannada", system-ui, sans-serif;
  
  /* Light Canvas */
  --bg: #ffffff;
  --bg-alt: #f5f5f7;
  --surface: #ffffff;
  --text: #1d1d1f;
  --text-secondary: #515154; /* Guaranteed >= 7:1 contrast on white */
  --accent: #0071e3;
  --link: #0066cc;
  --hairline: rgba(0, 0, 0, 0.12);

  /* Clinical Severity Palette */
  --sev-critical: #d70015;
  --sev-high: #c93400;
  --sev-moderate: #8a5a00;
  --sev-low: #1d7d3f;

  /* Geometry & Physics */
  --radius-card: 24px;
  --radius-input: 12px;
  --radius-pill: 980px;
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.08);
  --ease: cubic-bezier(0.28, 0.11, 0.32, 1);
}
```

### Dark Mode & High Contrast
- **Dark Mode:** Deep black (`#000000`) canvas, surface elevation (`#1c1c1e`), subdued hairlines, and brightened accent (`#2997ff`).
- **High-Contrast Toggle:** Forces pure monochromatic contrast with reinforced border strokes for seniors with cataract or low-vision conditions.

---

## 3. Typography & Senior Accessibility

- **Responsive Clamps:** Hero headline scales smoothly `clamp(40px, 7vw, 80px)` with -0.02em tracking.
- **Senior App Baseline:** Starts at **22px minimum** (scalable up to 200% via live text slider).
- **Indic Script Support:** Enhanced line height (`line-height: 1.65`) for Devanagari and Kannada to prevent matra clipping.
- **Non-Color Severity Signals:** Severity levels are never signaled by color alone; every alert pairs a distinct geometric icon, an explicit text label (CRITICAL, HIGH, MODERATE, LOW), and clear source citations.

---

## 4. Reusable Component Primitives

1. **PillButton (`frontend/src/components/PillButton.tsx`)**: High-contrast, tactile, min-height 44px (56px for senior app).
2. **CardTile (`frontend/src/components/CardTile.tsx`)**: 24px rounded elevation tile with subtle hairline border.
3. **BentoGrid (`frontend/src/components/BentoGrid.tsx`)**: 12-column responsive layout grid for feature storytelling.
4. **InsetGroupedList (`frontend/src/components/InsetGroupedList.tsx`)**: iOS-inspired settings-style grouping for medications and audit trails.
5. **SegmentedControl (`frontend/src/components/SegmentedControl.tsx`)**: Smooth tab-switching for languages and views.
6. **DeviceFrame (`frontend/src/components/DeviceFrame.tsx`)**: Generic stylized device enclosure for embedding the live WhatsApp simulator on the landing page.
7. **VoiceMicButton (`frontend/src/components/VoiceMicButton.tsx`)**: Prominent 72px tactile voice button with breathing animation during active recording.

---

## 5. Multi-App Architecture

- **`apps/landing/`**: Public showcase with hero, 3-step story (Say it, Check it, Share it), bento grid, interactive simulator preview, and safety footnotes.
- **`apps/senior/`**: One-action-per-screen, huge touch targets (>= 56px), live speech & text side-by-side, text-size scaling, high contrast toggle, and instant "Call Caregiver" / "Emergency 112" buttons.
- **`apps/caregiver/`**: Action-oriented dashboard with full medication profile, active risk flags, change log, symptom history, and one-click Doctor Discussion Guide PDF export.
- **`apps/clinician/`**: Desktop split-view / mobile swipe card interface with 10-second undo, required clinical reason tags on rejection, and audited unmasking.
- **`apps/admin/`**: Governed feedback queue reviewing rule change proposals and real-time LLM gateway usage/budget telemetry.
- **`apps/simulator/`**: WhatsApp-style conversational channel emulator supporting voice note uploads, photos, quick replies, and scenario auto-loading.

