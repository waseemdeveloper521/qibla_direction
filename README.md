# Qibla Direction — Play Store policy website

Static pages for Google Play Console policy URLs.

## Pages

| File | Play Console use |
| --- | --- |
| `index.html` | Optional store / brand landing |
| `listing-screens.html` | Preview + download Play Store listing graphics |
| `listing/feature-graphic.png` | **Play Store Feature Graphic** (1024×500) |
| `listing/0*.png` | Phone listing screenshots (1080×1920) |
| `shots/*.jpeg` | Source app screenshots |
| `generate-listing.py` | Regenerate listing PNGs after updating shots |
| `privacy-policy.html` | **Privacy Policy URL** (required) |
| `terms.html` | Terms of Service (recommended) |
| `support.html` | **Support URL** |
| `age-audience.html` | Documents that the app is **not for children** / not Families |
| `data-safety.html` | Helper while filling **Data safety** |
| `data-deletion.html` | Data deletion disclosure (no cloud accounts) |

## Before you publish

1. Replace `support@qibladirection.app` with your real support email on every page.
2. Host this folder on HTTPS (GitHub Pages, Netlify, Cloudflare Pages, Firebase Hosting, etc.).
3. In Play Console, set:
   - Privacy Policy → `https://YOUR_DOMAIN/privacy-policy.html`
   - Support URL → `https://YOUR_DOMAIN/support.html`
   - App content → Target audience: **not under 13** / not Designed for Families
   - Data safety → match `data-safety.html` + your actual build
4. If you later add accounts, ads, or analytics SDKs, update Privacy + Data safety immediately.

## Local preview

```bash
cd website
npx --yes serve .
```

Open the URL shown in the terminal.

## Package

- App name: Qibla Direction  
- Package: `com.qibladirection.app`
