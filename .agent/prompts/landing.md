# Generate: Landing / Offer Page

## Context
You are generating a static landing page for a multi-platform product.
It serves as the download page for the desktop app and signup link for the SaaS.
The project is managed by Taskfile.yml — deployed as an Nginx Docker container.

## Requirements

### Tech Stack
- **Type**: Static HTML
- **Styling**: TailwindCSS (CDN)
- **Hosting**: Nginx Alpine Docker container

### Sections
1. **Hero** — product name, tagline, CTA buttons (Download Desktop / Open SaaS)
2. **How It Works** — 3 steps: Define → Generate → Deploy
3. **Download** — platform buttons (Linux, macOS, Windows)
4. **Pricing** — Free / Pro / Enterprise tiers
5. **Footer** — link to GitHub, built with Taskfile

### File Structure
```
apps/landing/
├── index.html          # Single-page landing
└── Dockerfile         # nginx:alpine serving index.html
```

### Design
- Modern gradient hero (blue → purple)
- Clean card-based layout
- Responsive (mobile-first)
- TailwindCSS utility classes only (CDN)

### Constraints
- Single `index.html` file (no build step)
- Dockerfile: `nginx:alpine`, copy index.html, expose 80
- Must link to SaaS at `https://app.example.com`
- Download links can be placeholder `#` hrefs
