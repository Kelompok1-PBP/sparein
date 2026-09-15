# Design System

Derived from the Sparein logo blue `#1581EE` and the near-black wordmark ink `#0A0A0A`. Everything below is a token; nothing in a template hardcodes a hex value.

![Sparein color tokens](brand/palette.svg)

## Color tokens

### Brand ramp

| Token | Hex | Use |
|---|---|---|
| `blue-50` | `#EFF7FE` | page sections, card backgrounds |
| `blue-100` | `#D7EBFD` | hover on subtle surfaces, chips |
| `blue-200` | `#B0D7FB` | borders on tinted surfaces |
| `blue-300` | `#7FBEF8` | disabled primary, decorative fills |
| `blue-400` | `#47A2F4` | focus ring |
| `blue-500` | `#1581EE` | primary: buttons, links, active nav |
| `blue-600` | `#0A66C9` | primary hover |
| `blue-700` | `#0A4FA0` | primary active, headings |
| `blue-800` | `#0D4280` | dark surface accents |
| `blue-900` | `#10386A` | dark section background |
| `blue-950` | `#0A2447` | footer, darkest surface |

### Semantic and neutral

| Token | Hex | Use |
|---|---|---|
| `success` | `#16A34A` | repair succeeded, impact gained |
| `warning` | `#D97706` | safety caution, tool required |
| `danger` | `#DC2626` | dangerous step, destructive action |
| `ink` | `#0A0A0A` | body text |
| `muted` | `#5B6472` | secondary text, metadata |
| `surface` | `#F7F9FC` | app background |
| `white` | `#FFFFFF` | cards, inputs |

### Contrast

`blue-500` on white is 3.6:1, which covers large text and UI components only. Body copy and small text on white use `ink`; text on `blue-500` uses white and passes at 4.5:1. Any new pairing gets checked before it ships.

Safety colors are never the only signal. A `danger` warning also carries an icon and the word "Danger", so the meaning survives a color-blind reader and a grayscale print.

## Tailwind config

```js
// tailwind.config.js
module.exports = {
  content: ['./**/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        blue: {
          50: '#EFF7FE', 100: '#D7EBFD', 200: '#B0D7FB', 300: '#7FBEF8',
          400: '#47A2F4', 500: '#1581EE', 600: '#0A66C9', 700: '#0A4FA0',
          800: '#0D4280', 900: '#10386A', 950: '#0A2447',
        },
        success: '#16A34A',
        warning: '#D97706',
        danger:  '#DC2626',
        ink:     '#0A0A0A',
        muted:   '#5B6472',
        surface: '#F7F9FC',
      },
      borderRadius: { card: '14px' },
    },
  },
}
```

## Typography

| Role | Size / line-height | Weight | Color |
|---|---|---|---|
| Display | 40 / 48 | 700 | `blue-700` |
| H1 | 32 / 40 | 700 | `ink` |
| H2 | 24 / 32 | 600 | `ink` |
| H3 | 20 / 28 | 600 | `ink` |
| Body | 16 / 26 | 400 | `ink` |
| Small | 14 / 20 | 400 | `muted` |
| Mono | 14 / 20 | 400 | `ink` |

Family: system UI stack for prose, `ui-monospace` for part numbers and step counters.

## Spacing and layout

4px base unit; use `4, 8, 12, 16, 24, 32, 48, 64`. Content column maxes out at `1120px`. Cards use `border-radius: 14px` and a single `1px` `blue-200` border. No drop shadows: the pages are dense with device photos, and shadows compete with them.

Breakpoints follow Tailwind defaults: `sm 640`, `md 768`, `lg 1024`, `xl 1280`. Every page is built mobile-first; the device catalog and part directory collapse to a single column below `md`.

## Components

| Component | Rules |
|---|---|
| Button primary | `blue-500` fill, white text, `blue-600` hover, `blue-400` focus ring, `blue-300` disabled |
| Button secondary | white fill, `blue-500` text, `blue-200` border |
| Card | white fill, `blue-200` border, 14px radius, 16px padding |
| Badge, difficulty | `Very easy`/`Easy` = `success`, `Moderate` = `warning`, `Difficult`/`Very difficult` = `danger`, all at 10% tint with full-strength text |
| Safety callout | left border 4px in `warning` or `danger`, matching icon, never collapsed behind a click |
| Empty state | `blue-50` surface, one sentence, one action |
| Form field | white fill, `blue-200` border, `blue-400` focus ring, error text in `danger` |

## Accessibility floor

Checked while each component is built, not audited at the end:

- Every interactive element is reachable and operable by keyboard, with a visible focus ring.
- Every image carries meaningful `alt`; decorative images carry `alt=""`.
- Forms use real `<label>` elements tied to their inputs.
- AJAX updates announce themselves through `aria-live="polite"` so a screen reader hears the new result count.
- Safety warnings never rely on color alone.

## Brand assets

| File | Use |
|---|---|
| `brand/sparein-lockup.svg` | icon and wordmark together, for the README header and the site header on light backgrounds |
| `brand/sparein-lockup-dark.svg` | same on dark backgrounds |
| `brand/sparein-icon.svg` | app icon, favicon source, light backgrounds |
| `brand/sparein-icon-dark.svg` | same on dark backgrounds |
| `brand/sparein-wordmark.svg` | header wordmark, light backgrounds |
| `brand/sparein-wordmark-dark.svg` | same on dark backgrounds |
| `brand/palette.svg` | token reference sheet |

Minimum clear space around the icon equals half its height. The wordmark is never stretched, recolored outside `ink` and white, or set over a busy photo without a solid plate behind it.
