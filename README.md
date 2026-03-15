<div align="center">

# VIGILHEX

**Global Airspace Anomaly Detection & Intelligence Platform**

[![Live App](https://img.shields.io/badge/🌐_LIVE-vigilhex.digital-E8500A?style=for-the-badge)](https://vigilhex.digital)
[![Telegram](https://img.shields.io/badge/📡_ALERTS-@vigilhex-2CA5E0?style=for-the-badge)](https://t.me/vigilhex)
[![License](https://img.shields.io/badge/License-AGPL_v3-141E22?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/pietrorenzii/vigilhex?style=for-the-badge&color=141E22)](https://github.com/pietrorenzii/vigilhex/stargazers)

</div>

---

![VIGILHEX Screenshot](docs/assets/screenshot.png)

---

VIGILHEX monitors global airspace 24/7 using only free, public ADS-B data — detecting transponder shutdowns, military movements, loitering near sensitive areas and emergency squawks in real time.

**Free. Open-source. No API key required.**

---

## Live

🌐 **[vigilhex.digital](https://vigilhex.digital)** — live map, click any aircraft for full details

📡 **[t.me/vigilhex](https://t.me/vigilhex)** — subscribe for automatic Telegram alerts

---

## What it detects

| Anomaly | Severity |
|---|---|
| Transponder off >5min | 🔴 CRITICAL |
| Squawk 7500 — Hijack | 🔴 CRITICAL |
| Squawk 7700 — Emergency | 🔴 CRITICAL |
| Squawk 7600 — Radio failure | 🟠 WARNING |
| Military aircraft no callsign | 🟠 WARNING |
| Unknown aircraft silent >2min | 🟠 WARNING |

---

## Deploy in 30 seconds
```bash
git clone https://github.com/pietrorenzii/vigilhex
```

Then deploy the `/docs` folder on [GitHub Pages](https://pages.github.com) — free, no server needed.

---

## Roadmap

- [x] Live world map with layer controls
- [x] Military / state / cargo / unknown classifier
- [x] Anomaly detection engine
- [x] Flight detail panel with route + ETA
- [x] Telegram alert bot
- [x] Cloudflare Worker proxy
- [x] Custom domain
- [ ] ADS-B Exchange military feed
- [ ] Historical analysis
- [ ] Daily intel report PDF
- [ ] Public REST API

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=pietrorenzii/vigilhex&type=Date)](https://star-history.com/#pietrorenzii/vigilhex&Date)

---

<div align="center">
<sub>AGPL-3.0 · Built with public data · Not affiliated with any government or military organization</sub>
</div>
