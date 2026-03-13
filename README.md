<div align="center">
```
 ██╗   ██╗██╗ ██████╗ ██╗██╗     ██╗  ██╗███████╗██╗  ██╗
 ██║   ██║██║██╔════╝ ██║██║     ██║  ██║██╔════╝╚██╗██╔╝
 ██║   ██║██║██║  ███╗██║██║     ███████║█████╗   ╚███╔╝
 ╚██╗ ██╔╝██║██║   ██║██║██║     ██╔══██║██╔══╝   ██╔██╗
  ╚████╔╝ ██║╚██████╔╝██║███████╗██║  ██║███████╗██╔╝ ██╗
   ╚═══╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
```

**Global Airspace Anomaly Detection & Intelligence Platform**

[![Live App](https://img.shields.io/badge/🌐_LIVE_APP-VIGILHEX-E8500A?style=for-the-badge)](https://vigilhex.streamlit.app)
[![License](https://img.shields.io/badge/License-AGPL_v3-141E22?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-141E22?style=for-the-badge&logo=python)](https://python.org)
[![OpenSky](https://img.shields.io/badge/Data-OpenSky_Network-141E22?style=for-the-badge)](https://opensky-network.org)

*Monitors global airspace 24/7 using public ADS-B data.
Detects transponder shutdowns, military movements, loitering near sensitive areas, and more.*

</div>

---

## What is VigilHex?

VigilHex is an open-source real-time flight anomaly detection platform built for:

- **Security researchers** and OSINT analysts
- **Defense professionals** and NATO observers
- **Investigative journalists** (Bellingcat-style aviation tracking)
- **Critical infrastructure operators**

It ingests live ADS-B data from public sources, classifies every aircraft (military / commercial / state / cargo / unknown), and scores each flight for anomalous behavior using rule-based detection and ML.

**Zero cost. Zero API keys required to start. 5-minute deploy.**

---

## Live Demo

> 🌐 **[vigilhex.streamlit.app](https://vigilhex.streamlit.app)**

The live demo shows real-time flights over Europe with anomaly scoring.
Toggle layers on/off: military, commercial, state, cargo, unknown.

---

## Detects

| Anomaly Type | Description | Severity |
|---|---|---|
| `TRANSPONDER_OFF` | Aircraft stops transmitting position | 🔴 CRITICAL |
| `SQUAWK_EMERGENCY` | 7500/7600/7700 squawk codes | 🔴 CRITICAL |
| `LOITERING` | Circular pattern near sensitive area | 🟠 WARNING |
| `RESTRICTED_ZONE` | Flight within buffer of military base / nuclear site | 🟠 WARNING |
| `NO_CALLSIGN` | Military/unknown aircraft with no identification | 🟠 WARNING |
| `UNUSUAL_ALTITUDE` | Rapid unexplained altitude changes | 🟠 WARNING |
| `UNUSUAL_SPEED` | Speed outside normal envelope | 🟡 WATCH |
| `NIGHT_FLIGHT` | Military flight over sensitive area at night | 🟡 WATCH |

---

## Aircraft Categories

| Icon | Category | Source |
|---|---|---|
| ⬡ 🔴 | **Military** | ICAO hex ranges + callsign patterns |
| ◈ 🟠 | **State / Government** | Callsign patterns (SAM, EXEC, FRON...) |
| ✈ ⚪ | **Commercial** | Standard IATA/ICAO callsign format |
| ▣ 🟣 | **Cargo** | Known cargo operator prefixes |
| ◇ 🟡 | **Private / GA** | Registration-style callsigns |
| ■ ⚫ | **Unknown** | No callsign, unidentified hex |

---

## Quick Deploy (5 minutes)

### Option 1 — Streamlit Cloud (recommended, free)

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Set main file: `frontend/streamlit_app.py`
5. Deploy

### Option 2 — Local
```bash
git clone https://github.com/pietrorenzii/vigilhex
cd vigilhex
pip install -r requirements.txt
streamlit run frontend/streamlit_app.py
```

---

## Architecture
```
OpenSky Network API ──► ingestion/opensky_collector.py
                              │
                              ▼
                   classifier/aircraft_classifier.py
                   (MILITARY / STATE / COMMERCIAL / CARGO / UNKNOWN)
                              │
                              ▼
                   anomaly/anomaly_detector.py
                   (rule-based scoring + ML)
                              │
                        ┌─────┴─────┐
                        ▼           ▼
               Streamlit Dashboard  Telegram Bot
               (live map + alerts)  (@VigilHexAlerts)
```

---

## Data Sources (all free, no key required)

| Source | Data | Key Required |
|---|---|---|
| [OpenSky Network](https://opensky-network.org/api) | Real-time ADS-B worldwide | No |
| [ADS-B Exchange](https://adsbexchange.com) | Unfiltered feed incl. military | Free tier |
| OpenStreetMap / Overpass | Sensitive area overlays | No |
| ICAO public registry | Aircraft classification | No |

---

## Roadmap

- [x] OpenSky real-time collector
- [x] Aircraft classifier (military/state/commercial/cargo/unknown)
- [x] Rule-based anomaly detection engine
- [x] Streamlit live dashboard with layer controls
- [ ] Telegram alert bot (@VigilHexAlerts)
- [ ] ADS-B Exchange military feed integration
- [ ] Isolation Forest ML model
- [ ] Daily PDF intel report
- [ ] REST API (public endpoints)
- [ ] Docker + docker-compose
- [ ] Historical 30-day analysis

---

## Enterprise / Government

VigilHex is open-source under AGPL-3.0.

For **hosted deployments, SLA, air-gapped installations, classified data integration,
or custom AOI configuration** — contact us.

Target clients: Ministries of Defence, NATO commands, Frontex, EU EEAS, critical infrastructure operators.

---

## Contributing

PRs welcome. See [docs/architecture.md](docs/architecture.md) for technical details.

If you find this useful, **star the repo** ⭐ — it helps with visibility.

---

<div align="center">
<sub>Built with public data · AGPL-3.0 · Not affiliated with any government or military organization</sub>
</div>
```
