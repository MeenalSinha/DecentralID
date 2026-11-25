# DecentralID UI Design System & Component Guidelines

**Product:** DecentralID — Portable, Privacy-Preserving Verifiable Credentials for Digital India  
**Version:** 2.0 Editorial System  
**Last Updated:** November 2026  

---

## 1. Design Philosophy & Aesthetic Identity

DecentralID's design philosophy rejects the generic "AI dashboard" look—avoiding excessive purple gradients, floating neon blobs, heavy glassmorphism, and oversized cards. Instead, it embodies the gravitas, precision, and restrained sophistication of an institutional trust network and a premium financial technology platform.

### Core Brand Attributes
1. **Trust & Credibility:** Clean, predictable surfaces, crisp typography, and high data readability suited for university chancellors, enterprise employers, and government agencies.
2. **Precision & Cryptographic Rigor:** Explicit status indicators, clear distinction between proof integrity and schema checks, and unambiguous technical audit data.
3. **Privacy by Architecture:** Immediate visual cues for salted commitments, zero personal data on-chain, and holder-controlled selective disclosure matrices.
4. **Editorial Restraint:** Warm off-white canvas, deep teal signature accent, muted status colors, and minimal elevation shadows.

---

## 2. Color System & Semantic Tokens

### Primary Palette
| Token | Hex | Role | Usage |
| :--- | :--- | :--- | :--- |
| `background` | `#F7F8F6` | Warm off-white | Main application canvas |
| `surface` | `#FFFFFF` | Pure white | Primary card & panel container |
| `surface-subtle` | `#F1F3F0` | Soft gray-green | Secondary sections, table headers, code blocks |
| `surface-hover` | `#E8ECE6` | Muted neutral | Hover states on interactive elements |
| `foreground` | `#17211F` | Deep charcoal | Primary text, titles, high-contrast labels |
| `foreground-secondary` | `#64716D` | Muted slate | Secondary descriptions, subheadings, labels |
| `foreground-muted` | `#8D9B97` | Soft stone | Helper text, placeholders, metadata keys |
| `border` | `#E4E8E4` | Neutral hairline | Standard component and table borders |
| `border-subtle` | `#EDF0ED` | Subtle hairline | Card inner dividing lines |
| `border-strong` | `#D0D6D0` | Medium border | Focused inputs and active boundaries |

### Signature Brand Accents
| Token | Hex | Role | Usage |
| :--- | :--- | :--- | :--- |
| `primary` | `#245C52` | Deep Teal | Core interactive actions, brand marks, active tabs |
| `primary-hover` | `#19483F` | Dark Forest Teal | Hover state for primary buttons |
| `primary-soft` | `#EAF2EF` | Pale Sage | Active nav backgrounds, primary badges |
| `primary-dark` | `#12352E` | Deep Cypress | Active pressed buttons, deep contrast elements |

### Semantic Feedback Tokens
| Semantic Role | Foreground Hex | Soft Background Hex | Border / Tone |
| :--- | :--- | :--- | :--- |
| **Success / Verified** | `#277451` | `#EBF5EF` | Restrained Emerald |
| **Warning / Pending** | `#A36B25` | `#FDF6E9` | Muted Amber |
| **Danger / Revoked** | `#B44848` | `#FBEFEF` | Muted Deep Red |
| **Info / Selective Disclosure** | `#2C5D88` | `#EEF4FA` | Slate Blue |

---

## 3. Typography & Scale

The typography stack relies on an institutional sans-serif font family (`Inter`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`) paired with a high-readability monospace font for cryptographic digests, wallet addresses, and W3C identifiers.

| Scale Name | Size / Leading | Weight | Usage |
| :--- | :--- | :--- | :--- |
| **Display Header** | `24px` / `32px` | Bold (`700`) | Main module page titles |
| **Section Header** | `18px` / `24px` | Semi-bold (`600`) | Card and major section headings |
| **Card Header** | `14px` / `20px` | Semi-bold (`600`) | Form group titles, sub-card titles |
| **Body Default** | `13px` / `18px` | Regular (`400`) | Standard body paragraphs, inputs |
| **Body Secondary** | `12px` / `16px` | Regular (`400`) | Supporting text, descriptions, table cells |
| **Overline / Label** | `10px` / `12px` | Bold (`700`) | Uppercase metadata headers, form labels |
| **Code / Digest** | `11px` / `16px` | Medium (`500`) | Hex hashes, DIDs, signatures, JSON payloads |

---

## 4. Reusable Component Specifications

The component library lives in `frontend/src/components/ui/` and is fully typed with TypeScript:

### 1. `Button`
- **Variants:** `primary` (deep teal), `secondary` (pale sage text), `outline` (white surface with hairline border), `ghost` (transparent text button), `danger` (muted red).
- **Sizes:** `sm` (compact actions), `md` (standard forms), `lg` (prominent CTAs).
- **Features:** Built-in `isLoading` spinner state, `leftIcon`, `rightIcon`, automatic disabled styling.

### 2. `Card`
- **Surfaces:** Pure white (`#FFFFFF`) with `12px` border radius (`rounded-card`) and a restrained hairline border (`border-border`).
- **Shadows:** Subtle elevation (`shadow-subtle` or `shadow-card`), zero heavy drop shadows.
- **Sub-components:** `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.

### 3. `Badge`
- **Variants:** `success`, `warning`, `danger`, `info`, `neutral`, `primary`.
- **Sizes:** `sm` (`11px`), `md` (`12px`).
- **Options:** Optional pulsing or static status `dot` indicator for on-chain status.

### 4. `Input` & `Select`
- **Heights:** Consistent `36px` to `40px` touch targets.
- **Styling:** Subtle focus ring (`focus:ring-2 focus:ring-primary/20 focus:border-primary`).
- **Features:** Integrated label, helper text, inline error message, and icon slots.

### 5. `Modal`
- **Backdrop:** Light neutral overlay (`bg-foreground/30 backdrop-blur-[2px]`).
- **Dialog:** Centered elevated card with keyboard `Escape` dismissal, focus trap, and responsive max-width (`sm`, `md`, `lg`, `xl`, `2xl`).

### 6. `Tabs`
- **Styling:** Underline or pill tabs with active indicator, smooth transitions, and numeric badge counters.

### 7. `Table`
- **Structure:** `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`.
- **Features:** Subtly tinted header (`#F1F3F0`), row hover transitions (`hover:bg-surface-subtle/60`), and overflow wrapper for mobile scrolling.

---

## 5. Layout Architecture

The application adopts a persistent desktop sidebar paired with a top application bar:

```
+-----------------------------------------------------------------------------------+
|  [DecentralID]  |  Header: Route Title & Breadcrumb     [Network] [Wallet Pill]   |
|                 +-----------------------------------------------------------------+
|  - Verify       |                                                                 |
|  - My Wallet    |  Main Content Canvas (max-w-7xl mx-auto, px-4 sm:px-6 py-8)    |
|  - Issuer       |                                                                 |
|  - Intelligence |                                                                 |
|                 |                                                                 |
|  [Network Card] |                                                                 |
+-----------------+-----------------------------------------------------------------+
|                 |  Footer: W3C VC v2.0 • EIP-712 Data Integrity • Zero PII        |
+-----------------------------------------------------------------------------------+
```

- **Sidebar:** Left navigation with collapsible width (`64px` icon-only vs `256px` expanded). Supports responsive slide-over drawer on mobile devices (`< 768px`).
- **Header:** Sticky top app bar providing contextual breadcrumbs, network status (Chain ID: `31337`), and connected wallet pill with 1-click address copy and disconnect dropdown.
- **Footer:** Single-line compact footer highlighting cryptographic standards compliance.

---

## 6. Accessibility & Responsiveness Guidelines

1. **Touch Targets:** Minimum 38x38px for touch surfaces on mobile viewports.
2. **Contrast Ratios:** Contrast between text (`#17211F`) and background (`#F7F8F6`) exceeds 14:1; secondary text (`#64716D`) exceeds 4.8:1 (WCAG AA).
3. **No Horizontal Scrolling:** All tables and payload code blocks feature contained horizontal scrollbars; layout containers remain fluid.
4. **Color Independence:** Status badges combine color, text labels, and distinct icon shapes so colorblind users can immediately distinguish valid vs invalid states.
