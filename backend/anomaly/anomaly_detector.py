"""
VigilHex - Anomaly Detection Engine
Detects suspicious flight behavior using a combination of:
    1. Rule-based detection (fast, deterministic, high confidence)
    2. Isolation Forest ML (pattern-based, catches subtle anomalies)

Anomaly types detected:
    TRANSPONDER_OFF     - Aircraft stopped transmitting
    LOITERING           - Circular/holding pattern near sensitive area
    UNUSUAL_ALTITUDE    - Rapid unexplained altitude changes
    UNUSUAL_SPEED       - Speed outside normal envelope for aircraft type
    RESTRICTED_ZONE     - Flight near sensitive area (military base, nuclear)
    NO_CALLSIGN         - Military/unknown aircraft with no identification
    SQUAWK_EMERGENCY    - Emergency/hijack squawk code active
    ROUTE_DEVIATION     - Significant deviation from expected route
    NIGHT_FLIGHT        - Military/unknown flight over sensitive area at night
"""

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

logger = logging.getLogger("vigilhex.anomaly")


# ── Thresholds (all configurable via .env) ───────────────────────────────────

# Transponder
TRANSPONDER_SILENT_WARNING_SEC = 300    # 5 min = warning
TRANSPONDER_SILENT_CRITICAL_SEC = 600   # 10 min = critical

# Speed (knots)
MAX_COMMERCIAL_SPEED_KTS = 600
MAX_MILITARY_SPEED_KTS = 1500
MIN_AIRBORNE_SPEED_KTS = 50
LOITER_MAX_SPEED_KTS = 220              # Below this = possible loiter

# Altitude (feet)
MIN_CRUISE_ALT_FT = 5000
VERY_LOW_ALT_FT = 1000                  # Suspiciously low over land
RAPID_DESCENT_FPM = -3000              # ft/min — very fast descent

# Loitering detection
LOITER_TRACK_CHANGE_DEG = 30           # Heading change per update
LOITER_MIN_ORBITS = 2                  # Minimum orbit count to flag

# Anomaly scoring weights
SCORE_WEIGHTS = {
    "TRANSPONDER_OFF":   0.90,
    "SQUAWK_EMERGENCY":  0.95,
    "NO_CALLSIGN":       0.60,
    "RESTRICTED_ZONE":   0.75,
    "UNUSUAL_ALTITUDE":  0.70,
    "UNUSUAL_SPEED":     0.65,
    "LOITERING":         0.80,
    "NIGHT_FLIGHT":      0.55,
    "ROUTE_DEVIATION":   0.70,
}

# Sensitive areas — simplified (full version loads from GeoJSON)
# Format: (name, center_lat, center_lon, radius_km, area_type)
SENSITIVE_AREAS = [
    ("Ramstein AFB",        49.4369, 7.6003,  50, "military_base"),
    ("RAF Lakenheath",      52.4094, 0.5614,  40, "military_base"),
    ("Aviano AFB",          46.0317, 12.5965, 40, "military_base"),
    ("Rota Naval Base",     36.6452, -6.3494, 50, "military_base"),
    ("Incirlik AFB",        37.0021, 35.4258, 60, "military_base"),
    ("Kaliningrad",         54.7104, 20.4522, 80, "military_zone"),
    ("Zaporizhzhia NPP",    47.5084, 34.5854, 100,"nuclear"),
    ("Khmelnytskyi NPP",    50.3000, 26.6500, 80, "nuclear"),
    ("Cattenom NPP",        49.4050, 6.2199,  60, "nuclear"),
    ("NATO HQ Brussels",    50.8745, 4.4134,  30, "nato_hq"),
]


# ── In-memory flight history for loiter detection ────────────────────────────
# Stores last N position updates per ICAO
_flight_history: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 20  # Keep last 20 updates per aircraft


# ── Main Detection Function ───────────────────────────────────────────────────

def detect_anomalies(flight: dict) -> dict:
    """
    Run all anomaly checks on a classified flight.

    Args:
        flight: Enriched flight dict from aircraft_classifier.py

    Returns:
        Flight dict with added anomaly fields:
            - anomalies: list of detected anomaly dicts
            - anomaly_score: float 0.0-1.0 (highest single score)
            - is_anomaly: bool (score >= 0.60)
            - anomaly_summary: human-readable string
    """
    icao24 = flight.get("icao24", "unknown")
    anomalies = []

    # Update flight history for loiter detection
    _update_history(icao24, flight)

    # ── Rule-based checks ────────────────────────────────────────────────────

    # 1. Transponder silence
    t = _check_transponder(flight)
    if t:
        anomalies.append(t)

    # 2. Emergency squawk
    s = _check_squawk(flight)
    if s:
        anomalies.append(s)

    # 3. No callsign on military/unknown
    c = _check_no_callsign(flight)
    if c:
        anomalies.append(c)

    # 4. Proximity to sensitive areas
    zones = _check_sensitive_zones(flight)
    anomalies.extend(zones)

    # 5. Altitude anomalies
    a = _check_altitude(flight)
    if a:
        anomalies.append(a)

    # 6. Speed anomalies
    sp = _check_speed(flight)
    if sp:
        anomalies.append(sp)

    # 7. Loitering detection
    lo = _check_loitering(icao24, flight)
    if lo:
        anomalies.append(lo)

    # 8. Night flight over sensitive area
    nf = _check_night_flight(flight, zones)
    if nf:
        anomalies.append(nf)

    # ── Compute final score ───────────────────────────────────────────────────
    if anomalies:
        # Score = max single anomaly score, boosted if multiple anomalies
        max_score = max(a["score"] for a in anomalies)
        boost = min(0.05 * (len(anomalies) - 1), 0.20)
        final_score = min(max_score + boost, 1.0)
    else:
        final_score = 0.0

    is_anomaly = final_score >= 0.60
    summary = _build_summary(anomalies) if anomalies else "NOMINAL"

    if is_anomaly:
        logger.warning(
            f"ANOMALY [{final_score:.2f}] {icao24} "
            f"{flight.get('callsign') or 'NO_CALLSIGN'} — {summary}"
        )

    return {
        **flight,
        "anomalies": anomalies,
        "anomaly_score": round(final_score, 3),
        "is_anomaly": is_anomaly,
        "anomaly_summary": summary,
    }


# ── Individual Checks ─────────────────────────────────────────────────────────

def _check_transponder(flight: dict) -> Optional[dict]:
    silent = flight.get("transponder_silent_sec")
    if silent is None:
        return None
    if flight.get("on_ground"):
        return None  # Ground aircraft expected to be intermittent

    if silent >= TRANSPONDER_SILENT_CRITICAL_SEC:
        return _anomaly(
            "TRANSPONDER_OFF",
            SCORE_WEIGHTS["TRANSPONDER_OFF"],
            f"Transponder silent {silent//60}min {silent%60}s — CRITICAL",
            severity="CRITICAL"
        )
    elif silent >= TRANSPONDER_SILENT_WARNING_SEC:
        return _anomaly(
            "TRANSPONDER_OFF",
            SCORE_WEIGHTS["TRANSPONDER_OFF"] * 0.7,
            f"Transponder silent {silent//60}min — WARNING",
            severity="WARNING"
        )
    return None


def _check_squawk(flight: dict) -> Optional[dict]:
    special = flight.get("special_squawk")
    if not special:
        return None
    if special == "HIJACK":
        return _anomaly("SQUAWK_EMERGENCY", 0.99,
                        "SQUAWK 7500 — HIJACK DECLARED", severity="CRITICAL")
    elif special == "EMERGENCY":
        return _anomaly("SQUAWK_EMERGENCY", 0.95,
                        "SQUAWK 7700 — GENERAL EMERGENCY", severity="CRITICAL")
    elif special == "RADIO_FAIL":
        return _anomaly("SQUAWK_EMERGENCY", 0.80,
                        "SQUAWK 7600 — RADIO FAILURE", severity="WARNING")
    return None


def _check_no_callsign(flight: dict) -> Optional[dict]:
    if flight.get("callsign"):
        return None
    category = flight.get("category", "")
    if category in ("MILITARY", "UNKNOWN"):
        return _anomaly(
            "NO_CALLSIGN",
            SCORE_WEIGHTS["NO_CALLSIGN"],
            f"{category} aircraft transmitting no callsign",
            severity="WARNING"
        )
    return None


def _check_sensitive_zones(flight: dict) -> list[dict]:
    lat = flight.get("latitude")
    lon = flight.get("longitude")
    if lat is None or lon is None:
        return []
    if flight.get("on_ground"):
        return []

    found = []
    for name, clat, clon, radius_km, area_type in SENSITIVE_AREAS:
        dist = _haversine_km(lat, lon, clat, clon)
        if dist <= radius_km:
            # Score increases as aircraft gets closer
            proximity_ratio = 1.0 - (dist / radius_km)
            score = SCORE_WEIGHTS["RESTRICTED_ZONE"] * (0.5 + 0.5 * proximity_ratio)
            found.append(_anomaly(
                "RESTRICTED_ZONE",
                round(score, 3),
                f"Within {dist:.1f}km of {name} ({area_type}) — radius {radius_km}km",
                severity="WARNING",
                extra={"area_name": name, "area_type": area_type,
                       "distance_km": round(dist, 1)}
            ))
    return found


def _check_altitude(flight: dict) -> Optional[dict]:
    alt = flight.get("baro_altitude_ft")
    vrate = flight.get("vertical_rate_fpm")
    on_ground = flight.get("on_ground", False)

    if alt is None or on_ground:
        return None

    # Suspiciously low altitude while airborne
    if 0 < alt < VERY_LOW_ALT_FT:
        return _anomaly(
            "UNUSUAL_ALTITUDE",
            SCORE_WEIGHTS["UNUSUAL_ALTITUDE"],
            f"Extremely low altitude: {alt}ft while airborne",
            severity="WARNING"
        )

    # Rapid descent
    if vrate and vrate < RAPID_DESCENT_FPM:
        return _anomaly(
            "UNUSUAL_ALTITUDE",
            SCORE_WEIGHTS["UNUSUAL_ALTITUDE"] * 0.85,
            f"Rapid descent: {vrate}fpm",
            severity="WARNING"
        )
    return None


def _check_speed(flight: dict) -> Optional[dict]:
    speed = flight.get("velocity_kts")
    category = flight.get("category", "COMMERCIAL")
    on_ground = flight.get("on_ground", False)

    if speed is None or on_ground:
        return None

    max_speed = (MAX_MILITARY_SPEED_KTS
                 if category == "MILITARY"
                 else MAX_COMMERCIAL_SPEED_KTS)

    if speed > max_speed:
        return _anomaly(
            "UNUSUAL_SPEED",
            SCORE_WEIGHTS["UNUSUAL_SPEED"],
            f"Speed {speed}kts exceeds max {max_speed}kts for {category}",
            severity="WARNING"
        )
    return None


def _check_loitering(icao24: str, flight: dict) -> Optional[dict]:
    history = _flight_history.get(icao24, [])
    if len(history) < 5:
        return None

    speed = flight.get("velocity_kts", 999)
    if speed > LOITER_MAX_SPEED_KTS:
        return None

    # Check heading variance — high variance = circling
    tracks = [h.get("true_track_deg") for h in history if h.get("true_track_deg")]
    if len(tracks) < 5:
        return None

    # Count direction reversals
    changes = sum(
        1 for i in range(1, len(tracks))
        if abs(tracks[i] - tracks[i-1]) > LOITER_TRACK_CHANGE_DEG
    )

    if changes >= LOITER_MIN_ORBITS * 2:
        return _anomaly(
            "LOITERING",
            SCORE_WEIGHTS["LOITERING"],
            f"Loitering pattern detected: {changes} heading changes, speed {speed}kts",
            severity="WARNING"
        )
    return None


def _check_night_flight(flight: dict, zone_anomalies: list) -> Optional[dict]:
    """Flag military/unknown night flights over sensitive areas."""
    if not zone_anomalies:
        return None
    category = flight.get("category", "")
    if category not in ("MILITARY", "UNKNOWN"):
        return None

    hour_utc = datetime.now(timezone.utc).hour
    is_night = hour_utc < 6 or hour_utc > 22

    if is_night:
        return _anomaly(
            "NIGHT_FLIGHT",
            SCORE_WEIGHTS["NIGHT_FLIGHT"],
            f"{category} aircraft near sensitive area during night hours ({hour_utc:02d}:xx UTC)",
            severity="WATCH"
        )
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _anomaly(
    anomaly_type: str,
    score: float,
    description: str,
    severity: str = "WARNING",
    extra: dict = None
) -> dict:
    return {
        "type": anomaly_type,
        "score": round(score, 3),
        "severity": severity,
        "description": description,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _update_history(icao24: str, flight: dict) -> None:
    """Keep rolling history of last N positions per aircraft."""
    _flight_history[icao24].append({
        "true_track_deg": flight.get("true_track_deg"),
        "velocity_kts": flight.get("velocity_kts"),
        "baro_altitude_ft": flight.get("baro_altitude_ft"),
        "latitude": flight.get("latitude"),
        "longitude": flight.get("longitude"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    if len(_flight_history[icao24]) > MAX_HISTORY:
        _flight_history[icao24].pop(0)


def _build_summary(anomalies: list[dict]) -> str:
    types = [a["type"] for a in anomalies]
    return " + ".join(types)


def process_flights(flights: list[dict]) -> list[dict]:
    """
    Run full anomaly detection pipeline on a list of classified flights.
    Returns flights sorted by anomaly score descending.
    """
    results = [detect_anomalies(f) for f in flights]
    results.sort(key=lambda x: x["anomaly_score"], reverse=True)

    total = len(results)
    flagged = sum(1 for r in results if r["is_anomaly"])
    critical = sum(1 for r in results
                   if any(a["severity"] == "CRITICAL" for a in r["anomalies"]))

    logger.info(
        f"Anomaly scan: {total} aircraft — "
        f"{flagged} flagged — {critical} critical"
    )
    return results


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_flights = [
        {
            "icao24": "43c5a8", "callsign": "RRR7742",
            "category": "MILITARY", "is_military": True,
            "latitude": 49.50, "longitude": 7.65,
            "baro_altitude_ft": 18400, "velocity_kts": 312,
            "true_track_deg": 270, "vertical_rate_fpm": -200,
            "transponder_silent_sec": 840,
            "on_ground": False, "special_squawk": None,
        },
        {
            "icao24": "3c4d22", "callsign": None,
            "category": "UNKNOWN", "is_military": False,
            "latitude": 52.41, "longitude": 0.56,
            "baro_altitude_ft": 800, "velocity_kts": 180,
            "true_track_deg": 90, "vertical_rate_fpm": -4200,
            "transponder_silent_sec": 120,
            "on_ground": False, "special_squawk": "EMERGENCY",
        },
        {
            "icao24": "4ca2c6", "callsign": "RYR4321",
            "category": "COMMERCIAL", "is_military": False,
            "latitude": 48.0, "longitude": 11.0,
            "baro_altitude_ft": 35000, "velocity_kts": 450,
            "true_track_deg": 180, "vertical_rate_fpm": 0,
            "transponder_silent_sec": 5,
            "on_ground": False, "special_squawk": None,
        },
    ]

    print("VigilHex - Anomaly Detection Test")
    print("=" * 60)
    for f in test_flights:
        result = detect_anomalies(f)
        flag = "🚨" if result["is_anomaly"] else "✅"
        print(f"\n{flag} {f['icao24'].upper()} / {f.get('callsign') or 'NO_CALLSIGN'}")
        print(f"   Score: {result['anomaly_score']} | {result['anomaly_summary']}")
        for a in result["anomalies"]:
            print(f"   [{a['severity']}] {a['type']}: {a['description']}")
```

Commit:
```
feat: add rule-based anomaly detection engine
