"""
VigilHex - Streamlit Dashboard (standalone test version)
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timezone

st.set_page_config(
    page_title="VIGILHEX — Global Airspace Intelligence",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap');
  html, body, [class*="css"] {
    background-color: #040506 !important;
    color: #7A8A8A !important;
    font-family: 'Share Tech Mono', monospace !important;
  }
  .stApp { background-color: #040506 !important; }
  [data-testid="stSidebar"] {
    background-color: #070A0B !important;
    border-right: 1px solid #141E22 !important;
  }
  [data-testid="stMetricValue"] {
    color: #C8D4D4 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
  }
  [data-testid="stMetricLabel"] {
    color: #4A5E68 !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
  }
  .hdr {
    font-family: 'Rajdhani', sans-serif;
    font-size: 26px; font-weight: 700;
    letter-spacing: 4px; color: #C8D4D4;
    border-bottom: 1px solid #141E22;
    padding-bottom: 8px; margin-bottom: 16px;
  }
  .hdr span { color: #E8500A; }
  .alert-critical {
    background: rgba(204,34,0,0.08);
    border: 1px solid #CC2200;
    border-left: 3px solid #CC2200;
    padding: 10px 14px; margin: 6px 0;
    font-size: 11px; color: #C8D4D4;
  }
  .alert-warning {
    background: rgba(232,80,10,0.06);
    border: 1px solid #E8500A;
    border-left: 3px solid #E8500A;
    padding: 10px 14px; margin: 6px 0;
    font-size: 11px; color: #C8D4D4;
  }
  .sec { font-size: 9px; color: #2A3840;
    letter-spacing: 3px; text-transform: uppercase;
    margin: 14px 0 8px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">● VIGIL<span>HEX</span> / GLOBAL AIRSPACE INTELLIGENCE</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec">// layer control</div>', unsafe_allow_html=True)
    show_commercial = st.checkbox("✈  COMMERCIAL",   value=True)
    show_military   = st.checkbox("⬡  MILITARY",     value=True)
    show_state      = st.checkbox("◈  STATE / GOV",  value=True)
    show_cargo      = st.checkbox("▣  CARGO",        value=True)
    show_unknown    = st.checkbox("■  UNKNOWN",      value=True)
    show_anomalies  = st.checkbox("🚨 ANOMALIES ONLY", value=False)
    st.markdown('<div class="sec">// sensitive areas</div>', unsafe_allow_html=True)
    show_bases   = st.checkbox("MILITARY BASES", value=True)
    show_nuclear = st.checkbox("NUCLEAR SITES",  value=True)
    st.markdown('<div class="sec">// controls</div>', unsafe_allow_html=True)
    if st.button("⟳  REFRESH"):
        st.cache_data.clear()
        st.rerun()

# ── Data fetch (inline, no imports from backend) ──────────────────────────────
@st.cache_data(ttl=60)
def fetch_flights():
    try:
        r = requests.get(
            "https://opensky-network.org/api/states/all",
            params={"lamin": 35.0, "lamax": 72.0, "lomin": -15.0, "lomax": 45.0},
            timeout=20,
            headers={"User-Agent": "VigilHex/0.1"}
        )
        r.raise_for_status()
        data = r.json()
        if not data or not data.get("states"):
            return []
        flights = []
        for s in data["states"]:
            if s[5] is None or s[6] is None:
                continue
            callsign = (s[1] or "").strip()
            silent = None
            if s[4]:
                silent = int(datetime.now(timezone.utc).timestamp()) - s[4]
            flights.append({
                "icao24":    s[0],
                "callsign":  callsign or None,
                "country":   s[2],
                "lon":       s[5],
                "lat":       s[6],
                "alt_ft":    round(s[7] * 3.28084) if s[7] else None,
                "spd_kts":   round(s[9] * 1.94384, 1) if s[9] else None,
                "on_ground": s[8],
                "squawk":    s[14],
                "silent_sec": silent,
            })
        return flights
    except Exception as e:
        st.error(f"Feed error: {e}")
        return []

# ── Classify inline ───────────────────────────────────────────────────────────
MIL_CALLSIGNS = ["RRR","GAF","FAF","USAF","REACH","DUKE","STEEL","NATO","MMM","JAKE","NAVY"]
STATE_CALLSIGNS = ["SAM","AF1","AF2","EXEC","GOVT","USCG","FRON"]
CARGO_PREFIXES  = ["UPS","FDX","CLX","BOX","GTI","DHL","MPH","ABX"]

MIL_HEX = [
    (0xAE0000, 0xAFFFFF),
    (0x43C000, 0x43CFFF),
    (0x3B0000, 0x3BFFFF),
    (0x140000, 0x157FFF),
]

def classify(f):
    icao = f["icao24"].upper()
    cs   = (f["callsign"] or "").upper()
    try:
        h = int(icao, 16)
        for lo, hi in MIL_HEX:
            if lo <= h <= hi:
                return "MILITARY"
    except Exception:
        pass
    if any(cs.startswith(p) for p in MIL_CALLSIGNS):   return "MILITARY"
    if any(cs.startswith(p) for p in STATE_CALLSIGNS):  return "STATE"
    if len(cs) >= 3 and cs[:3] in CARGO_PREFIXES:       return "CARGO"
    if not cs:                                           return "UNKNOWN"
    return "COMMERCIAL"

def is_anomaly(f, cat):
    if (f["silent_sec"] or 0) > 300 and not f["on_ground"]: return True
    if f["squawk"] in ("7500","7600","7700"):                return True
    if cat in ("MILITARY","UNKNOWN") and not f["callsign"]:  return True
    return False

# ── Load & process ────────────────────────────────────────────────────────────
with st.spinner("FETCHING LIVE FEED..."):
    raw = fetch_flights()

flights = []
for f in raw:
    cat = classify(f)
    ano = is_anomaly(f, cat)
    flights.append({**f, "category": cat, "anomaly": ano})

# ── Stats ─────────────────────────────────────────────────────────────────────
total    = len(flights)
military = sum(1 for f in flights if f["category"] == "MILITARY")
anomalies= sum(1 for f in flights if f["anomaly"])
unknown  = sum(1 for f in flights if f["category"] == "UNKNOWN")
xpdr_off = sum(1 for f in flights if (f["silent_sec"] or 0) > 300)

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("TRACKED",   f"{total:,}")
c2.metric("MILITARY",  f"{military}")
c3.metric("ANOMALIES", f"{anomalies}")
c4.metric("UNKNOWN",   f"{unknown}")
c5.metric("XPDR OFF",  f"{xpdr_off}")

# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">// live world map</div>', unsafe_allow_html=True)

COLORS = {
    "COMMERCIAL": "#2A4050",
    "MILITARY":   "#CC2200",
    "STATE":      "#886600",
    "CARGO":      "#4A2A6A",
    "UNKNOWN":    "#2A3840",
}
RADIUS = {"COMMERCIAL":3,"MILITARY":6,"STATE":5,"CARGO":4,"UNKNOWN":4}

SENSITIVE = [
    ("Ramstein AFB",     49.44,  7.60,  50, "military"),
    ("RAF Lakenheath",   52.41,  0.56,  40, "military"),
    ("Aviano AFB",       46.03, 12.60,  40, "military"),
    ("Incirlik AFB",     37.00, 35.43,  60, "military"),
    ("Kaliningrad",      54.71, 20.45,  80, "military"),
    ("Zaporizhzhia NPP", 47.51, 34.59, 100, "nuclear"),
    ("Cattenom NPP",     49.41,  6.22,  60, "nuclear"),
]

m = folium.Map(
    location=[48.0, 14.0],
    zoom_start=5,
    tiles="CartoDB dark_matter",
    prefer_canvas=True,
)

# Sensitive areas
for name, clat, clon, rkm, atype in SENSITIVE:
    if atype == "military" and not show_bases:   continue
    if atype == "nuclear"  and not show_nuclear: continue
    color = "#CC2200" if atype == "nuclear" else "#1A4060"
    folium.Circle(
        location=[clat, clon],
        radius=rkm * 1000,
        color=color, weight=1,
        fill=True, fill_color=color, fill_opacity=0.12,
        tooltip=f"{name}",
    ).add_to(m)

# Aircraft
plotted = 0
for f in flights:
    cat = f["category"]
    ano = f["anomaly"]

    if show_anomalies and not ano: continue
    if not show_anomalies:
        if cat == "COMMERCIAL" and not show_commercial: continue
        if cat == "MILITARY"   and not show_military:   continue
        if cat == "STATE"      and not show_state:      continue
        if cat == "CARGO"      and not show_cargo:      continue
        if cat == "UNKNOWN"    and not show_unknown:    continue
    if f["on_ground"]: continue

    color  = "#E8500A" if ano else COLORS.get(cat, "#2A3840")
    radius = (RADIUS.get(cat, 3) + 3) if ano else RADIUS.get(cat, 3)

    tip = (
        f"<div style='font-family:monospace;font-size:11px;"
        f"background:#040506;color:#C8D4D4;padding:8px;"
        f"border:1px solid #E8500A;min-width:180px'>"
        f"<b style='color:#E8500A'>{f['callsign'] or 'NO CALLSIGN'}</b><br>"
        f"ICAO: {f['icao24'].upper()}<br>"
        f"CAT: {cat}<br>"
        f"ALT: {f['alt_ft'] or '—'}ft · SPD: {f['spd_kts'] or '—'}kts<br>"
        f"COUNTRY: {f['country']}<br>"
        f"{'<span style=color:#CC2200>⚠ ANOMALY</span>' if ano else 'NOMINAL'}"
        f"</div>"
    )

    folium.CircleMarker(
        location=[f["lat"], f["lon"]],
        radius=radius,
        color=color, fill=True,
        fill_color=color, fill_opacity=0.85,
        weight=2 if ano else 1,
        tooltip=folium.Tooltip(tip, sticky=True),
    ).add_to(m)
    plotted += 1

st_folium(m, width=None, height=560, returned_objects=[])
st.caption(
    f"Showing {plotted} aircraft · "
    f"Updated: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC · "
    f"Source: OpenSky Network"
)

# ── Anomaly feed ──────────────────────────────────────────────────────────────
flagged = [f for f in flights if f["anomaly"]]
if flagged:
    st.markdown('<div class="sec">// active anomalies</div>', unsafe_allow_html=True)
    for f in flagged[:15]:
        sev = "critical" if (f["silent_sec"] or 0) > 600 or f["squawk"] in ("7500","7700") else "warning"
        st.markdown(f"""
        <div class="alert-{sev}">
          <b style='color:#C8D4D4'>{f['callsign'] or 'NO CALLSIGN'}</b>
          · {f['icao24'].upper()} · {f['category']} · {f['country']}<br>
          <span style='color:#4A5E68;font-size:10px'>
            ALT: {f['alt_ft'] or '—'}ft · SPD: {f['spd_kts'] or '—'}kts
            {f'· XPDR SILENT {f["silent_sec"]}s' if (f["silent_sec"] or 0) > 300 else ''}
            {f'· SQUAWK {f["squawk"]}' if f["squawk"] in ("7500","7600","7700") else ''}
          </span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<div class="sec">// no anomalies detected</div>', unsafe_allow_html=True)
```
