"""
VigilHex - Streamlit MVP Dashboard
Real-time global flight anomaly detection interface.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import sys
import os
import time
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.ingestion.opensky_collector import fetch_europe_flights
from backend.classifier.aircraft_classifier import classify_batch
from backend.anomaly.anomaly_detector import process_flights

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VIGILHEX — Global Airspace Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — dark ops theme ───────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap');

  html, body, [class*="css"] {
    background-color: #040506 !important;
    color: #7A8A8A !important;
    font-family: 'Share Tech Mono', monospace !important;
  }
  .stApp { background-color: #040506 !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #070A0B !important;
    border-right: 1px solid #141E22 !important;
  }

  /* Metrics */
  [data-testid="stMetric"] {
    background-color: #0A0E10;
    border: 1px solid #141E22;
    border-radius: 0px;
    padding: 12px;
  }
  [data-testid="stMetricValue"] {
    color: #C8D4D4 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
  }
  [data-testid="stMetricLabel"] {
    color: #4A5E68 !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
  }

  /* Header */
  .vigilhex-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #C8D4D4;
    border-bottom: 1px solid #141E22;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }
  .vigilhex-header span { color: #E8500A; }

  /* Alert boxes */
  .alert-critical {
    background: rgba(204,34,0,0.08);
    border: 1px solid #CC2200;
    border-left: 3px solid #CC2200;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 11px;
    color: #C8D4D4;
  }
  .alert-warning {
    background: rgba(232,80,10,0.06);
    border: 1px solid #E8500A;
    border-left: 3px solid #E8500A;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 11px;
    color: #C8D4D4;
  }
  .tag {
    display: inline-block;
    font-size: 9px;
    padding: 1px 6px;
    border: 1px solid;
    margin-right: 6px;
    letter-spacing: 1px;
  }
  .tag-mil  { color: #FF3311; border-color: #CC2200; }
  .tag-ano  { color: #E8500A; border-color: #E8500A; }
  .tag-sta  { color: #886600; border-color: #664400; }
  .tag-unk  { color: #4A5E68; border-color: #2A3840; }
  .section-label {
    font-size: 9px; color: #2A3840; letter-spacing: 3px;
    text-transform: uppercase; margin: 14px 0 8px;
  }
  div[data-testid="stCheckbox"] label {
    font-size: 11px !important;
    color: #7A8A8A !important;
  }
  .stButton button {
    background: #0A0E10 !important;
    border: 1px solid #1A2830 !important;
    color: #7A8A8A !important;
    border-radius: 0px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
  }
  .stButton button:hover {
    border-color: #E8500A !important;
    color: #E8500A !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vigilhex-header">
  ● VIGIL<span>HEX</span> &nbsp;/&nbsp; GLOBAL AIRSPACE INTELLIGENCE
</div>
""", unsafe_allow_html=True)


# ── Sidebar — Layer Controls ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">// system</div>', unsafe_allow_html=True)
    auto_refresh = st.toggle("AUTO REFRESH (60s)", value=False)
    if st.button("⟳  REFRESH NOW"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="section-label">// layer control</div>', unsafe_allow_html=True)
    show_commercial = st.checkbox("✈  COMMERCIAL",  value=True)
    show_military   = st.checkbox("⬡  MILITARY",    value=True)
    show_state      = st.checkbox("◈  STATE / GOV", value=True)
    show_cargo      = st.checkbox("▣  CARGO",       value=True)
    show_private    = st.checkbox("◇  PRIVATE / GA",value=True)
    show_unknown    = st.checkbox("■  UNKNOWN",     value=True)
    show_anomalies  = st.checkbox("🚨 ANOMALIES ONLY (override)", value=False)

    st.markdown('<div class="section-label">// sensitive areas</div>', unsafe_allow_html=True)
    show_mil_bases  = st.checkbox("MILITARY BASES",  value=True)
    show_nuclear    = st.checkbox("NUCLEAR SITES",   value=True)

    st.markdown('<div class="section-label">// presets</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ISR MODE"):
            show_military = True
            show_anomalies = True
    with col2:
        if st.button("FULL VIEW"):
            show_commercial = True


# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_flights():
    """Fetch, classify and score all flights. Cached 60s."""
    raw = fetch_europe_flights()
    if not raw:
        return []
    classified = classify_batch(raw)
    processed  = process_flights(classified)
    return processed


with st.spinner("FETCHING LIVE FEED..."):
    flights = load_flights()


# ── Compute stats ─────────────────────────────────────────────────────────────
total      = len(flights)
military   = sum(1 for f in flights if f.get("category") == "MILITARY")
anomalies  = sum(1 for f in flights if f.get("is_anomaly"))
critical   = sum(1 for f in flights
               if any(a["severity"] == "CRITICAL"
                      for a in f.get("anomalies", [])))
unknown    = sum(1 for f in flights if f.get("category") == "UNKNOWN")
xpdr_off   = sum(1 for f in flights
               if (f.get("transponder_silent_sec") or 0) > 300)


# ── Top metrics bar ───────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("TRACKED",    f"{total:,}")
c2.metric("MILITARY",   f"{military}",  delta=None)
c3.metric("ANOMALIES",  f"{anomalies}", delta=f"+{anomalies}" if anomalies else None)
c4.metric("CRITICAL",   f"{critical}",  delta="ALERT" if critical else None)
c5.metric("UNKNOWN",    f"{unknown}")
c6.metric("XPDR OFF",   f"{xpdr_off}",  delta="⚠" if xpdr_off else None)


# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// live world map</div>',
            unsafe_allow_html=True)

# Build folium map — dark tiles
m = folium.Map(
    location=[48.0, 14.0],
    zoom_start=5,
    tiles="CartoDB dark_matter",
    prefer_canvas=True,
)

# ── Color & icon mapping ──────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "COMMERCIAL": "#2A4050",
    "MILITARY":   "#CC2200",
    "STATE":      "#886600",
    "CARGO":      "#4A2A6A",
    "PRIVATE":    "#1A3A2A",
    "UNKNOWN":    "#2A3840",
}

CATEGORY_RADIUS = {
    "COMMERCIAL": 3,
    "MILITARY":   5,
    "STATE":      5,
    "CARGO":      4,
    "PRIVATE":    3,
    "UNKNOWN":    4,
}

# ── Sensitive area overlays ───────────────────────────────────────────────────
from backend.anomaly.anomaly_detector import SENSITIVE_AREAS

if show_mil_bases or show_nuclear:
    for name, clat, clon, radius_km, area_type in SENSITIVE_AREAS:
        if area_type == "military_base" and not show_mil_bases:
            continue
        if area_type == "nuclear" and not show_nuclear:
            continue

        color = "#1A2830" if area_type == "nuclear" else "#1A2A30"
        border = "#CC2200" if area_type == "nuclear" else "#1A4060"

        folium.Circle(
            location=[clat, clon],
            radius=radius_km * 1000,
            color=border,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.15,
            tooltip=f"{name} ({area_type})",
        ).add_to(m)


# ── Plot aircraft ─────────────────────────────────────────────────────────────
def should_show(flight: dict) -> bool:
    if show_anomalies:
        return flight.get("is_anomaly", False)
    cat = flight.get("category", "")
    if cat == "COMMERCIAL" and not show_commercial: return False
    if cat == "MILITARY"   and not show_military:   return False
    if cat == "STATE"      and not show_state:      return False
    if cat == "CARGO"      and not show_cargo:      return False
    if cat == "PRIVATE"    and not show_private:    return False
    if cat == "UNKNOWN"    and not show_unknown:    return False
    return True


plotted = 0
for flight in flights:
    lat = flight.get("latitude")
    lon = flight.get("longitude")
    if lat is None or lon is None:
        continue
    if not should_show(flight):
        continue

    cat       = flight.get("category", "UNKNOWN")
    is_anomaly= flight.get("is_anomaly", False)
    callsign  = flight.get("callsign") or "NO CALLSIGN"
    icao24    = flight.get("icao24", "").upper()
    score     = flight.get("anomaly_score", 0.0)
    alt       = flight.get("baro_altitude_ft")
    spd       = flight.get("velocity_kts")
    summary   = flight.get("anomaly_summary", "NOMINAL")

    color  = "#E8500A" if is_anomaly else CATEGORY_COLORS.get(cat, "#2A3840")
    radius = (CATEGORY_RADIUS.get(cat, 3) + 3) if is_anomaly else CATEGORY_RADIUS.get(cat, 3)

    tooltip_html = f"""
    <div style='font-family:monospace;font-size:11px;background:#040506;
                color:#C8D4D4;padding:8px;border:1px solid #E8500A;
                min-width:200px'>
      <b style='color:#E8500A'>{callsign}</b><br>
      ICAO: {icao24}<br>
      CAT: {cat} &nbsp;|&nbsp; SCORE: {score:.2f}<br>
      ALT: {alt or '—'}ft &nbsp;|&nbsp; SPD: {spd or '—'}kts<br>
      <span style='color:{"#CC2200" if is_anomaly else "#2A3840"}'>
        {summary}
      </span>
    </div>
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.85,
        weight=1 if not is_anomaly else 2,
        tooltip=folium.Tooltip(tooltip_html, sticky=True),
    ).add_to(m)
    plotted += 1

# Render map
st_folium(m, width=None, height=560, returned_objects=[])

st.caption(
    f"Showing {plotted} aircraft · "
    f"Last update: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC · "
    f"Source: OpenSky Network"
)


# ── Anomaly Feed ──────────────────────────────────────────────────────────────
flagged = [f for f in flights if f.get("is_anomaly")]

if flagged:
    st.markdown(
        '<div class="section-label">// active anomalies</div>',
        unsafe_allow_html=True
    )
    for f in flagged[:20]:
        sev = "critical" if any(
            a["severity"] == "CRITICAL" for a in f.get("anomalies", [])
        ) else "warning"

        cat_tag = f"<span class='tag tag-mil'>{f.get('category')}</span>"
        cs  = f.get("callsign") or "NO CALLSIGN"
        ic  = (f.get("icao24") or "").upper()
        sc  = f.get("anomaly_score", 0)
        sm  = f.get("anomaly_summary", "")
        alt = f.get("baro_altitude_ft")
        spd = f.get("velocity_kts")
        cty = f.get("origin_country", "")

        st.markdown(f"""
        <div class="alert-{sev}">
          {cat_tag}
          <b style='color:#C8D4D4'>{cs}</b>
          &nbsp;·&nbsp; {ic}
          &nbsp;·&nbsp; {cty}
          &nbsp;&nbsp;
          <span style='color:#E8500A'>SCORE: {sc:.2f}</span>
          <br>
          <span style='color:#4A5E68;font-size:10px'>
            {sm}
            &nbsp;·&nbsp; ALT: {alt or '—'}ft
            &nbsp;·&nbsp; SPD: {spd or '—'}kts
          </span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="section-label">// no anomalies detected</div>',
        unsafe_allow_html=True
    )


# ── Auto refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
```

Commit:
```
feat: add Streamlit MVP dashboard with live map and layer controls
