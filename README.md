<div align="center">

# VIGILHEX

**Global Airspace Anomaly Detection & Intelligence Platform**

[![Live App](https://img.shields.io/badge/🌐_LIVE_APP-vigilhex.streamlit.app-E8500A?style=for-the-badge)](https://vigilhex.streamlit.app)
[![Telegram](https://img.shields.io/badge/📡_ALERTS-Telegram_Channel-141E22?style=for-the-badge)](https://t.me/vigilhex)
[![License](https://img.shields.io/badge/License-AGPL_v3-141E22?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/pietrorenzii/vigilhex?style=for-the-badge&color=141E22)](https://github.com/pietrorenzii/vigilhex/stargazers)

</div>

---

<!-- Sostituisci questo commento con la tua GIF demo una volta che Streamlit è live -->
<!-- ![VigilHex Demo](docs/assets/demo.gif) -->

---

VigilHex monitors global airspace **24/7 using only free, public ADS-B data**.

It classifies every aircraft in real time — military, commercial, state, cargo, unknown — and scores each flight for anomalous behavior: transponder shutdowns, loitering near sensitive areas, unusual routes, emergency squawks.

**Free. Open-source. 5-minute deploy.**

---

## Screenshots

<!-- Aggiungi i tuoi screenshot qui dopo il deploy, esempio: -->
<!-- ![Dashboard](docs/assets/screenshot_map.png) -->
<!-- ![Anomaly Feed](docs/assets/screenshot_anomalies.png) -->

*Screenshots coming soon — deploy the live app to see it in action.*

---

## Features

- 🗺️ **Live World Map** — real-time aircraft positions, layer toggle on/off
- 🔴 **Military Tracker** — dedicated layer with ICAO hex range detection
- 🚨 **Anomaly Detection** — transponder off, loitering, altitude drops, restricted zones
- 🟠 **State / Gov Aircraft** — VIP transport, police, Frontex, EU institutional
- ⚫ **Unknown / No Callsign** — maximum attention flag
- 📡 **Telegram Alerts** — public channel, automatic real-time notifications
- 📊 **Daily Intel Report** — auto-generated PDF digest of top anomalies
- 🔌 **REST API** — public endpoints for third-party integrations

---

## Anomaly Types

| Type | Description | Severity |
|---|---|---|
| `TRANSPONDER_OFF` | Aircraft stops transmitting | 🔴 CRITICAL |
| `SQUAWK_EMERGENCY` | 7500 / 7600 / 7700 active | 🔴 CRITICAL |
| `LOITERING` | Circular pattern near sensitive area | 🟠 WARNING |
| `RESTRICTED_ZONE` | Inside buffer of military base or nuclear site | 🟠 WARNING |
| `NO_CALLSIGN` | Military or unknown with no identification | 🟠 WARNING |
| `UNUSUAL_ALTITUDE` | Rapid unexplained altitude change | 🟠 WARNING |
| `NIGHT_FLIGHT` | Military over sensitive area at night | 🟡 WATCH |

---

## Quick Start
```bash
git clone https://github.com/pietrorenzii/vigilhex
cd vigilhex
pip install -r requirements.txt
streamlit run frontend/streamlit_app.py
```

Or deploy free in 1 click on **[Streamlit Cloud](https://share.streamlit.io)** —
set main file to `frontend/streamlit_app.py`.

---

## Data Sources

All free. No API keys required to start.

| Source | Data |
|---|---|
| [OpenSky Network](https://opensky-network.org/api) | Real-time ADS-B worldwide |
| [ADS-B Exchange](https://adsbexchange.com) | Unfiltered feed including military |
| OpenStreetMap | Sensitive area overlays |
| ICAO public registry | Aircraft classification |

---

## Architecture
```
OpenSky Network ──► opensky_collector.py
                          │
                          ▼
             aircraft_classifier.py
             MILITARY · STATE · COMMERCIAL · CARGO · UNKNOWN
                          │
                          ▼
             anomaly_detector.py
             rule-based scoring + Isolation Forest ML
                          │
                  ┌───────┴───────┐
                  ▼               ▼
        Streamlit Dashboard   Telegram Bot
        live map + alerts     @VigilHexAlerts
```

---

## Roadmap

- [x] OpenSky real-time collector
- [x] Aircraft classifier
- [x] Anomaly detection engine
- [x] Streamlit live dashboard
- [ ] Telegram alert bot
- [ ] ADS-B Exchange military feed
- [ ] Isolation Forest ML model
- [ ] Daily PDF intel report
- [ ] REST API
- [ ] Docker deploy

---

## Enterprise

VigilHex is open-source under AGPL-3.0.

For hosted deployments, SLA, air-gapped installations, classified data integration or custom AOI — **[open an issue](https://github.com/pietrorenzii/vigilhex/issues)** or contact via Telegram.

Target clients: Ministries of Defence · NATO commands · Frontex · EU EEAS · Critical infrastructure operators.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=pietrorenzii/vigilhex&type=Date)](https://star-history.com/#pietrorenzii/vigilhex&Date)

---

<div align="center">
<sub>Built with public data only · AGPL-3.0 · Not affiliated with any government or military organization</sub>
</div>
```

---
