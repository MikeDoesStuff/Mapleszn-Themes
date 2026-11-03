# Maple Themes for t3code

Dark and light themes for [t3code](https://github.com/pingdotgg/t3code), built around muted maple-leaf accents on grey bases that don't turn brown. They pair well with the Maple Mono font.

| Theme | Made by | Dark background | Dark accent | Description |
|---|---|---|---|---|
| **Maple Cinder** | ChatGPT | `#36393D` | `#E4A18B` | Graphite-grey with soft terracotta and copper, an autumnal accent rather than a brown background. |
| **Maple Ember** | ChatGPT | `#30333B` | `#D8A778` | Soft charcoal-slate dark theme with amber and copper accents, inspired by maple leaves without an overly brown or green palette. |
| **Maple Oat** | ChatGPT | `#393936` | `#DBBC91` | Soft warm greige-grey and pale honey accents, without turning brown. |
| **Maple Mist** | ChatGPT | `#343B46` | `#A9C7DE` | Cool, airy blue-grey charcoal with subdued icy-blue accents. |
| **Maple Twilight** | ChatGPT | `#353540` | `#D3ADD9` | Smoky blue-plum charcoal with muted lavender and apricot highlights. |
| **Maple Frost** | Claude | `#2B323B` | `#F19485` | Cool frosted blue-grey with a red maple-leaf accent: first frost on autumn leaves. |
| **Maple Dusk** | Claude | `#332F3A` | `#F0AE77` | Smoky plum-slate with glowing apricot: autumn leaves at sunset. |
| **Maple Momiji** | Claude | `#312E2C` | `#F18B71` | Neutral ink-grey with Japanese-maple vermilion and a whisper of warmth. |
| **Maple Sugar** | Claude | `#2A3339` | `#F1BD73` | Cool slate with sugar-maple gold, complementary blue and amber without the brown. |

## Install

Import any file from [`themes/`](themes) into t3code's theme settings. Each file has a dark base and a `light` variant, so the theme follows t3code's light, dark or system appearance setting.

## Preview

Open [`preview/index.html`](preview/index.html) in a browser to click through every theme in a mock t3code window, with contrast ratios for the fixed syntax colours.

## Design notes

- Each theme is a tinted neutral ramp plus one leaf-coloured accent, the same neutral/primary split used by Material's theme builder. The newer themes are generated in OKLCH.
- Frost and Sugar pair a warm accent with a cool blue-slate base, so the accent reads as maple without the background going brown.
- Error, warning and update colours are nudged up to 15° toward the accent, like Material's `harmonize()`.
- Light variants keep each theme's accent hue. Red, copper, blue and plum accents are darkened for white button text. Gold and amber accents stay bright with dark text, because darkening them turns them brown.
- t3code's syntax colours can't be themed, and the comment grey has the lowest contrast. Keep `codeBackground` and `canvas` around OKLCH L 0.30–0.32 so comments stay readable. In light mode t3code darkens its syntax colours to 4.5:1 on any light code background, so light `codeBackground` values only need to stay pale.
