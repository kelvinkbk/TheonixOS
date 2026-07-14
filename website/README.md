# Theonix OS — Website

The official website for **Theonix OS**, a modern Arch-based Linux distribution
(KDE Plasma 6, Wayland, rolling release). Dark futuristic glassmorphism design with
blue/cyan accents. Static, fast, SEO-optimised and accessible.

## Pages (17)

| File | Purpose |
|------|---------|
| `index.html` | Home — hero, terminal animation, feature cards, screenshots carousel, install steps, community |
| `download.html` | Landing — specs, four action buttons (Download / Release Notes / SHA256 / Repository), requirements, highlights |
| `download-start.html` | Download interstitial — progress animation, 3s auto-start, success state, manual fallback |
| `verify.html` | Verify the ISO checksum on Linux / macOS / Windows |
| `features.html` | The actual, shipped features + technical stack |
| `screenshots.html` | Gallery with a keyboard-navigable **lightbox** |
| `documentation.html` | Install, boot USB, BIOS/UEFI, Secure Boot, dual-boot, packages, updates, recovery, troubleshooting |
| `roadmap.html` | Shipped / in-progress / planned |
| `changelog.html` | Release-history timeline |
| `release-notes.html` | Long-form 1.0 "Genesis" notes |
| `community.html` | Channels and ways to contribute |
| `contributors.html` | Project lead + upstream credits |
| `faq.html` | FAQ (with FAQPage JSON-LD) |
| `blog.html` | Blog index + launch announcement |
| `about.html` | Mission, vision, goals, developer, philosophy |
| `brand.html` | Brand guide — logo, palette, type, components |
| `404.html` | Not-found page |

## Architecture

- **Static HTML**, no framework. Every page is independently crawlable.
- **Shared chrome** — the navbar and footer are defined **once** in
  `assets/js/components.js` and injected into every page (`<div data-site-header>` /
  `<div data-site-footer>`). No duplicated nav/footer markup to maintain. The nav is
  `position:fixed` and the footer is the last element, so injection causes no layout shift.
- **Tailwind CSS, precompiled** to a single minified `assets/css/theonix.min.css`
  (no runtime CDN). The design-system layer (tokens, glassmorphism, components,
  animations) lives in `src/input.css`; theme extensions in `tailwind.config.js`.
- **Vanilla JS** (`assets/js/main.js`) — nav state, mobile menu, scroll reveal, card
  spotlight, screenshots carousel, terminal typing, copy buttons, lightbox gallery
  (keyboard + fullscreen), and the download mirror selector.

## Download flow

The ISO is hosted on **Hugging Face**. All download CTAs across the site point to the
`download.html` landing page (specs + four action buttons). Its primary **Download
TheonixOS** button opens `download-start.html`, a professional interstitial that:

- shows the logo, version, release date, size and checksum link,
- runs a 3-second progress animation, then **auto-starts the download** by pointing the
  browser at the ISO,
- shows a **success** message and always offers a **manual** download button as a fallback.

Canonical asset URLs (edit these in one place if the host ever changes —
`download.html`, `download-start.html`, `verify.html`, home JSON-LD):

| Asset | URL |
|-------|-----|
| ISO | `https://huggingface.co/datasets/kelvinkbk/TheonixOS-1.0/resolve/main/TheonixOS-1.0.iso` |
| Repository | `https://huggingface.co/datasets/kelvinkbk/TheonixOS-1.0` |
| SHA256SUMS | `.../resolve/main/SHA256SUMS` (raw) · `.../blob/main/SHA256SUMS` (view) |
| README / CHANGELOG | `.../blob/main/README.md` · `.../blob/main/CHANGELOG.md` |

## Build the CSS

```bash
cd website
npm install
npm run build:css     # → assets/css/theonix.min.css (minified)
npm run watch:css     # rebuild on change during development
```

`tailwind.config.js` scans `./*.html` and `./assets/js/*.js` (so classes inside the
injected nav/footer are included).

## Run locally

```bash
cd website
python3 -m http.server 8080     # http://localhost:8080
```

## Performance, SEO & accessibility

- Precompiled CSS, deferred JS, non-blocking font loading, SVG assets — no render-blocking CDN.
- Per-page `title`/`description`/canonical, Open Graph + Twitter cards, JSON-LD
  (SoftwareApplication, WebSite, FAQPage), `robots.txt`, `sitemap.xml`.
- Semantic landmarks, one `<h1>` per page, skip link, `:focus-visible` rings, ARIA on
  interactive controls, keyboard-navigable carousel/lightbox, and `prefers-reduced-motion` support.

## Factual integrity

The site describes only what Theonix OS actually is. It contains **no invented ratings,
download counts, user counts, benchmarks, awards or reviews**. The planned AI assistant
is always labelled *Planned*. Keep it that way when editing.

## Assets

Real raster screenshots can replace the styled `.shot` placeholders in `index.html`
and `screenshots.html` (give each lightbox trigger `data-img="assets/img/…"`). A raster
`og-image.png` (1200×630) can replace `assets/img/og-image.svg` for maximum social-preview
compatibility.

---

© Theonix OS · Created by Kelvin Benny Koshy · Released under the GPL.
