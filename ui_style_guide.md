# UI Style Guide

This document describes the UI aesthetic, theme, and component patterns used in the reference app. Replicate this style in any new Mantine-based app.

---

## Stack

- **UI library:** Mantine (v7+) — `@mantine/core`, `@mantine/hooks`, `@mantine/dates`, `@mantine/notifications`
- **Icons:** `@tabler/icons-react` — use `ThemeIcon` wrapper with `variant="transparent"` for nav icons
- **Utility CSS:** Tailwind CSS (used alongside Mantine, not instead of it)
- **Font:** Inter (Google Fonts, `display: "swap"`, subset: latin)
- **Color scheme:** **Light only** — `forceColorScheme="light"` on `MantineProvider`, `defaultColorScheme="light"` on `ColorSchemeScript`

---

## Organization Context

This app belongs to the **University of Massachusetts** (UMass). The brand palette is built around UMass institutional colors. The logo is a PNG (`umass-logo.png`) rendered via an `<Image>` component at `width={48}` in the header.

---

## Mantine Theme

Apply this theme via `createTheme` and pass it to `MantineProvider`:

```ts
import { createTheme } from "@mantine/core";

export const theme = createTheme({
  primaryColor: "umgreen",
  primaryShade: 6,
  cursorType: "pointer",
  colors: {
    umblue: [
      "#ebf5ff",
      "#d5e7fa",
      "#a4cdf7",
      "#72b2f6",
      "#4e9cf5",
      "#3b8ef5",
      "#3187f6",
      "#2674dc",
      "#1b67c4",
      "#0059ad",
    ],
    ummaroon: [
      "#ffecef",
      "#f7d8dd",
      "#ebaeb7",
      "#e08290",
      "#d75c6e",
      "#d24559",
      "#d0394e",
      "#b92b40",
      "#a62438",
      "#92192f",
    ],
    umgreen: [
      "#69E8D7",
      "#57E5D2",
      "#34DFC8",
      "#1FC7B0",
      "#19A391",
      "#148071",
      "#179281",
      "#19A391",
      "#1DB9A4",
      "#20CBB4",
    ],
    umyellow: [
      "#fff8e0",
      "#fff0ca",
      "#ffdf9a",
      "#fdcd64",
      "#fcbe38",
      "#fcb51b",
      "#fcb006",
      "#e19a00",
      "#c88900",
      "#ad7500",
    ],
    umpink: [
      "#ffeaf0",
      "#fdd5dd",
      "#f4a7b8",
      "#ec7891",
      "#e5506f",
      "#e1375a",
      "#e02850",
      "#c71a41",
      "#b21139",
      "#9e0230",
    ],
  },
  // ... component overrides below
});
```

### CSS Variables Resolver

Register a CSS variables resolver to expose `--mantine-color-secondary` (mapped to `umblue[6]`), used for outline button/icon borders and hover outlines:

```ts
import { CSSVariablesResolver } from "@mantine/core";

export const resolver: CSSVariablesResolver = (theme) => ({
  variables: {
    "--mantine-color-secondary": theme.colors.umblue[6],
  },
  light: {
    "--mantine-color-placeholder": theme.colors.gray[7],
    "--mantine-color-dimmed": theme.colors.gray[7],
  },
  dark: {},
});
```

---

## Color Reference

| Name       | Main Hex  | Role                                                   |
| ---------- | --------- | ------------------------------------------------------ |
| `umgreen`  | `#148071` | Primary color (buttons, active states)                 |
| `umblue`   | `#005EB8` | Secondary color (outlines, nav hover, avatar gradient) |
| `ummaroon` | `#9D2235` | Accent (report/data icons)                             |
| `umyellow` | `#FCB316` | Accent (home/dashboard icons)                          |
| `umpink`   | `#DF2049` | Accent (secondary actions)                             |

All named colors are also available as Tailwind utilities (e.g., `bg-umblue-100`, `hover:bg-umblue-200`).

---

## Global CSS

```css
body {
  background: #f5f5f5 !important; /* light gray page background */
  overflow-y: hidden;
}

/* Uniform placeholder color across all browsers */
*::placeholder {
  color: var(--mantine-color-gray-7) !important;
  opacity: 1;
}

/* Fade-in utility class */
.fadeIn {
  animation: 90ms ease-out fadeIn;
}

@keyframes fadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}
```

---

## Component Defaults & Overrides

Apply these in the `components` section of `createTheme`.

### Button

- `variant="outline"` → `2px solid umblue[6]` border
- Filled buttons: subtle `text-shadow: 1px 1px #1116` on label for contrast
- Hover/active: 2px solid outline at 4px offset — primary color for filled, `--mantine-color-secondary` for outline/default variants
- Disabled buttons: gray-7 text, no shadow

### ActionIcon

- Same outline hover/active pattern as Button
- `variant="outline"` → `2px solid umblue[6]`

### TextInput / Textarea / NumberInput

- `placeholder: "Enter a value"`
- Read-only state: `background-color: gray[1]`, `cursor: not-allowed`
- Error state: placeholder takes on `--mantine-color-error` color

### Autocomplete / Select

- `limit: 15`
- `placeholder`: `"Enter a value"` (Autocomplete) / `"Select a value"` (Select)
- `comboboxProps: { shadow: "xs" }`
- Custom fuzzy/sorted filter function on options

### DatePickerInput

- `valueFormat: "MM/DD/YYYY"`
- `placeholder: "Pick a date"`
- `clearable: true`
- `popoverProps: { shadow: "sm" }`

### Tooltip

- `events: { hover: true, focus: true, touch: false }` — tooltips appear on hover AND keyboard focus

### Modal

- `closeButtonProps: { "aria-label": "Close modal" }`

---

## Layout Structure (AppShell)

The app uses Mantine's `AppShell` with a fixed header and a collapsible side navbar.

```
┌──────────────────────────────────────────────────────┐
│ HEADER (height: 68px, drop-shadow)                   │
│  [Logo 48px] [App Title] | [Burger] ... [UserMenu]  │
├──────────────────────────────────────────────────────┤
│ NAVBAR (width: 300px, no border, drop-shadow)        │
│  ┌ Expanded: full NavLink list (text + icon)         │
│  └ Collapsed: narrow 64px icon-only strip            │
│                                                      │
│ MAIN CONTENT                                         │
│  White rounded card, drop-shadow                     │
│  Shifts left margin: 64px (narrow nav) → 0 (open)   │
│  Padding: sm, pt: 20, overflow-x: hidden             │
│  Height: calc(100vh - 92px)                          │
└──────────────────────────────────────────────────────┘
```

**Key layout values:**

- Header height: `68px`
- Navbar expanded width: `300px`
- Narrow nav strip width: `64px` (`w-16`)
- Main content card: `bg-white rounded drop-shadow`
- Content area height: `calc(100vh - 92px)` with `overflowX: hidden`
- Transition: `100ms ease-out` (or `0` with `useReducedMotion`)

### Navbar behavior

- **Expanded:** Full-width `NavLink` list with icon + label. `NavLink` uses `color="umblue"`, `autoContrast`, `c="black"`, hover: `bg-umblue-100`, active: `bg-umblue-200`
- **Collapsed:** A fixed narrow strip (`NarrowNavigation`) with icon-only `UnstyledButton` links. Hover: `bg-umblue-200 drop-shadow-md`, active: `bg-umblue-300`
- Collapsed icon buttons show tooltips on the right (`position="right-start"`, `transition: "pop"`)
- Mobile (<500px): narrow nav hidden; expanded nav fills the screen

### Navigation icons use `ThemeIcon` with brand colors:

- Home → `umyellow`
- Search/Database → `umgreen`
- New record → `umblue`
- Reports → `ummaroon`

---

## User Avatar / Menu

- `Avatar` with `variant="gradient"`, gradient `from: "umblue.6"` → `to: "umgreen.4"`, `radius="xl"`
- Displays user initials with `text-shadow: 1px 1px #1116`
- Menu dropdown: 280px wide, `shadow="md"`, anchored to the right edge
- Menu items: Settings (indigo icon), Sign Out (grape icon), hover: `bg-umblue-100`

---

## Tailwind Color Utilities

Register these in `tailwind.config.ts` so Mantine color names work as Tailwind class utilities:

```ts
colors: {
  umblueMain: "#005EB8",
  umblue:   { 100: "#ebf5ff", 200: "#d5e7fa", 300: "#a4cdf7", ... 900: "#1b67c4" },
  ummaroonMain: "#9D2235",
  ummaroon: { 100: "#ffecef", ... 900: "#a62438" },
  umgreenMain: "#148071",
  umgreen:  { 100: "#edfcfa", ... 900: "#31ad9a" },
  umyellowMain: "#FCB316",
  umyellow: { 100: "#fff8e0", ... 900: "#c88900" },
  umpinkMain: "#DF2049",
  umpink:   { 100: "#ffeaf0", ... 900: "#b21139" },
}
```

---

## Summary of Key Aesthetic Decisions

- **Light mode only** — no dark mode toggle
- **Body background** is light gray (`#f5f5f5`), content panels are white cards
- **Primary action color is teal-green** (`umgreen`), secondary is blue (`umblue`)
- **Outline borders** are always `2px solid` — never thinner
- **Hover/focus outlines** on buttons and action icons at 4px offset — accessibility-first
- **Placeholders** are consistently gray-7 across all browsers via explicit cross-browser CSS
- **Read-only inputs** are visually distinct (gray-1 background, not-allowed cursor)
- **Reduced motion** is always respected via `useReducedMotion()` — pass `0` duration when true
- **Tooltips** appear on both hover AND keyboard focus
- **Tabler icons** are the icon library — always wrap nav icons in `ThemeIcon variant="transparent"`
- **Inter** is the only font — no custom heading font
