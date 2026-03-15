<div align="center">

# VIGILHEX

**Global Airspace Anomaly Detection & Intelligence Platform**

[![Live App](https://img.shields.io/badge/🌐_LIVE_APP-vigilhex.digital-E8500A?style=for-the-badge)](https://vigilhex.digital)
[![Telegram](https://img.shields.io/badge/📡_ALERTS-@vigilhex-2CA5E0?style=for-the-badge)](https://t.me/vigilhex)
[![License](https://img.shields.io/badge/License-AGPL_v3-141E22?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/pietrorenzii/vigilhex?style=for-the-badge&color=141E22)](https://github.com/pietrorenzii/vigilhex/stargazers)

</div>

---

<!-- Sostituisci con il tuo screenshot o GIF una volta pronto -->
<!-- ![VIGILHEX Demo](docs/assets/demo.gif) -->

![VIGILHEX Screenshot](docs/assets/screenshot.png)

---

VIGILHEX monitors global airspace 24/7 using only free, public ADS-B data, detecting anomalous behavior in real time — transponder shutdowns, military movements, loitering near sensitive areas, emergency squawks.

**Free. Open-source. No API key required.**

---

## 🌐 Live Demo

> **[vigilhex.digital](https://vigilhex.digital)**

Real-time map of military, state, cargo and unknown aircraft worldwide.
Click any aircraft to see full flight data, route and anomaly details.

## 📡 Telegram Alerts

> **[t.me/vigilhex](https://t.me/vigilhex)**

Subscribe to receive automatic real-time alerts for:
- 🔴 Transponder shutdowns
- 🔴 Emergency squawks (7500/7600/7700)
- 🟠 Military aircraft with no callsign
- 🟠 Aircraft near sensitive areas

---

## Features

- 🗺️ **Live World Map** — real-time positions, layer toggle on/off
- 🔴 **Military Tracker** — ICAO hex range detection + callsign patterns
- 🚨 **Anomaly Detection** — transponder off, emergency squawks, no callsign
- 🟠 **State / Gov Aircraft** — VIP transport, Frontex, EU institutional
- ⚫ **Unknown / No Callsign** — maximum attention flag
- 📡 **Telegram Alerts** — automatic real-time notifications to public channel
- ✈️ **Flight Detail Panel** — route, progress, ETA, full telemetry on click

---

## Anomaly Types

| Type | Description | Severity |
|---|---|---|
| `TRANSPONDER_OFF` | Aircraft stops transmitting >5min | 🔴 CRITICAL |
| `SQUAWK_7500` | Hijack declared | 🔴 CRITICAL |
| `SQUAWK_7700` | General emergency | 🔴 CRITICAL |
| `SQUAWK_7600` | Radio failure | 🟠 WARNING |
| `MILITARY_NO_CALLSIGN` | Military aircraft with no identification | 🟠 WARNING |
| `UNKNOWN_SILENT` | Unknown aircraft transponder silent >2min | 🟠 WARNING |

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
