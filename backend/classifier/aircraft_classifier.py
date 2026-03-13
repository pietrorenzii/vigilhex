"""
VigilHex - Aircraft Classifier
Classifies aircraft into categories based on ICAO hex, callsign patterns,
squawk codes, and known military/state aircraft lists.

Categories:
    MILITARY    - Military aircraft (known hex ranges + callsign patterns)
    STATE       - Government/state aircraft (VIP transport, police, etc.)
    COMMERCIAL  - Scheduled airline flights
    CARGO       - Freight/cargo operators
    PRIVATE     - General aviation / business jets
    UNKNOWN     - No callsign, unidentified hex, suspicious
"""

import re
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger("vigilhex.classifier")


# ── Category Enum ────────────────────────────────────────────────────────────

class AircraftCategory(str, Enum):
    MILITARY   = "MILITARY"
    STATE      = "STATE"
    COMMERCIAL = "COMMERCIAL"
    CARGO      = "CARGO"
    PRIVATE    = "PRIVATE"
    UNKNOWN    = "UNKNOWN"


# ── ICAO hex ranges for military aircraft by country ─────────────────────────
# Source: public ICAO documentation + ADS-B Exchange research
# Format: (start_hex, end_hex, country, description)

MILITARY_HEX_RANGES = [
    # United States Military
    ("AE0000", "AFFFFF", "USA", "US Military"),
    # United Kingdom Military
    ("43C000", "43CFFF", "GBR", "UK Military"),
    # France Military
    ("3B0000", "3BFFFF", "FRA", "French Military"),
    # Germany Military
    ("3DC000", "3DCFFF", "DEU", "German Military"),
    # Italy Military
    ("500000", "500FFF", "ITA", "Italian Military"),
    # Russia Military
    ("140000", "157FFF", "RUS", "Russian Military"),
    # NATO AWACS
    ("45D000", "45D0FF", "NATO", "NATO AWACS"),
]

# Known military callsign prefixes (regex patterns)
MILITARY_CALLSIGN_PATTERNS = [
    r"^RRR\d+",      # UK Royal Air Force
    r"^GAF\d+",      # German Air Force (Luftwaffe)
    r"^FAF\d+",      # French Air Force
    r"^IAM\d+",      # Italian Air Force
    r"^USAF\d*",     # US Air Force
    r"^DUKE\d+",     # US Military
    r"^REACH\d+",    # USAF Air Mobility Command
    r"^STEEL\d+",    # USAF
    r"^SWORD\d+",    # USAF
    r"^JAKE\d+",     # US Navy
    r"^NAVY\d+",     # US Navy generic
    r"^TURC\d+",     # Turkish Air Force
    r"^NATO\d*",     # NATO flights
    r"^SHAPE\d*",    # NATO Supreme HQ
    r"^MMM\d+",      # Italian Military
    r"^CTM\d+",      # Portuguese Air Force
    r"^CASA\d+",     # Spanish Air Force
    r"^EVY\d+",      # Dutch Air Force
    r"^BAFE\d+",     # Belgian Air Force
]

# State/Government aircraft callsign patterns
STATE_CALLSIGN_PATTERNS = [
    r"^SAM\d+",      # US Special Air Mission (Presidential/VIP)
    r"^AF1$",        # Air Force One
    r"^AF2$",        # Air Force Two
    r"^EXEC\d+",     # Executive transport
    r"^GOVT\d*",     # Government generic
    r"^POL\d+",      # Police
    r"^GUARD\d+",    # Coast Guard / National Guard
    r"^USCG\d+",     # US Coast Guard
    r"^FRON\d+",     # Frontex (EU Border Agency)
    r"^EU\d+",       # EU institutional flights
]

# Known cargo/freight ICAO airline codes (first 3 chars of callsign)
CARGO_PREFIXES = [
    "UPS", "FDX", "CLX", "BOX", "GTI",  # UPS, FedEx, Cargolux, CargoJet, Atlas Air
    "MPH", "ABX", "KMI", "PAC", "SWN",  # Various cargo
    "TGX", "DHL", "BCS", "CSN",         # DHL, etc.
    "ACA", "ACN",                         # Air Canada Cargo
]

# Squawk codes with special meaning
SPECIAL_SQUAWKS = {
    "7500": "HIJACK",       # Aircraft hijacking
    "7600": "RADIO_FAIL",   # Radio failure
    "7700": "EMERGENCY",    # General emergency
    "0000": "NO_SQUAWK",    # No squawk assigned
    "2000": "IFR_OCEANIC",  # IFR oceanic
    "1200": "VFR",          # VFR flight
}


# ── Core Classification Logic ─────────────────────────────────────────────────

def classify_aircraft(flight: dict) -> dict:
    """
    Classify a flight dict (from OpenSky collector) into a category.

    Args:
        flight: Flight dict from opensky_collector.py

    Returns:
        Original flight dict enriched with:
            - category: AircraftCategory
            - category_confidence: float 0.0-1.0
            - category_reason: str explanation
            - special_squawk: str or None
            - is_military: bool
            - is_state: bool
            - priority_flag: bool (needs extra attention)
    """
    icao24 = (flight.get("icao24") or "").upper()
    callsign = (flight.get("callsign") or "").upper().strip()
    squawk = flight.get("squawk") or ""
    origin_country = flight.get("origin_country") or ""

    # Check special squawk first — always flagged regardless of category
    special_squawk = SPECIAL_SQUAWKS.get(squawk)

    # Run classification checks in priority order
    category, confidence, reason = _classify(icao24, callsign, origin_country)

    # Enrich flight dict
    result = {
        **flight,
        "category": category.value,
        "category_confidence": confidence,
        "category_reason": reason,
        "special_squawk": special_squawk,
        "is_military": category == AircraftCategory.MILITARY,
        "is_state": category == AircraftCategory.STATE,
        "priority_flag": _should_flag_priority(flight, category, special_squawk),
    }

    if category in (AircraftCategory.MILITARY, AircraftCategory.STATE):
        logger.debug(
            f"[{category.value}] {icao24} / {callsign or 'NO_CALLSIGN'} "
            f"— {reason} (confidence={confidence})"
        )

    return result


def _classify(
    icao24: str,
    callsign: str,
    origin_country: str
) -> tuple[AircraftCategory, float, str]:
    """
    Core classification logic. Returns (category, confidence, reason).
    """

    # 1. Check ICAO hex range (highest confidence for military)
    hex_match = _check_military_hex(icao24)
    if hex_match:
        return AircraftCategory.MILITARY, 0.95, f"ICAO hex range: {hex_match}"

    # 2. Check military callsign patterns
    if callsign:
        mil_pattern = _match_patterns(callsign, MILITARY_CALLSIGN_PATTERNS)
        if mil_pattern:
            return AircraftCategory.MILITARY, 0.90, f"Military callsign pattern: {mil_pattern}"

    # 3. Check state/government callsign patterns
    if callsign:
        state_pattern = _match_patterns(callsign, STATE_CALLSIGN_PATTERNS)
        if state_pattern:
            return AircraftCategory.STATE, 0.88, f"State callsign pattern: {state_pattern}"

    # 4. Check cargo prefixes
    if callsign and len(callsign) >= 3:
        if callsign[:3] in CARGO_PREFIXES:
            return AircraftCategory.CARGO, 0.85, f"Cargo operator prefix: {callsign[:3]}"

    # 5. No callsign = UNKNOWN (suspicious)
    if not callsign:
        return AircraftCategory.UNKNOWN, 0.70, "No callsign transmitted"

    # 6. Callsign looks like airline (3 letters + digits = IATA/ICAO format)
    if re.match(r"^[A-Z]{3}\d{1,4}[A-Z]?$", callsign):
        return AircraftCategory.COMMERCIAL, 0.80, "Standard airline callsign format"

    # 7. Callsign looks like registration (private, e.g. G-ABCD, N12345)
    if re.match(r"^[A-Z]-[A-Z]{4}$|^[A-Z]\d+", callsign):
        return AircraftCategory.PRIVATE, 0.75, "Registration-style callsign (private/GA)"

    # 8. Default: commercial with low confidence
    return AircraftCategory.COMMERCIAL, 0.50, "Default classification (callsign present)"


def _check_military_hex(icao24: str) -> Optional[str]:
    """
    Check if ICAO hex falls within known military ranges.
    Returns description string if match found, None otherwise.
    """
    if len(icao24) != 6:
        return None
    try:
        hex_int = int(icao24, 16)
        for start, end, country, desc in MILITARY_HEX_RANGES:
            if int(start, 16) <= hex_int <= int(end, 16):
                return f"{desc} ({country})"
    except ValueError:
        pass
    return None


def _match_patterns(text: str, patterns: list[str]) -> Optional[str]:
    """
    Try matching text against a list of regex patterns.
    Returns the matched pattern string or None.
    """
    for pattern in patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return pattern
    return None


def _should_flag_priority(
    flight: dict,
    category: AircraftCategory,
    special_squawk: Optional[str]
) -> bool:
    """
    Determine if flight needs priority attention regardless of anomaly score.
    """
    # Always flag emergency squawks
    if special_squawk in ("HIJACK", "EMERGENCY"):
        return True

    # Always flag military with no callsign
    if category == AircraftCategory.MILITARY and not flight.get("callsign"):
        return True

    # Flag aircraft on ground with emergency squawk
    if special_squawk == "EMERGENCY" and flight.get("on_ground"):
        return True

    return False


def classify_batch(flights: list[dict]) -> list[dict]:
    """
    Classify a list of flights. Returns enriched list.
    Logs summary statistics.
    """
    if not flights:
        return []

    results = [classify_aircraft(f) for f in flights]

    # Log summary
    from collections import Counter
    cats = Counter(r["category"] for r in results)
    priority = sum(1 for r in results if r["priority_flag"])

    logger.info(
        f"Classification complete: {len(results)} aircraft — "
        + ", ".join(f"{k}:{v}" for k, v in cats.most_common())
        + f" — Priority flags: {priority}"
    )

    return results


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test cases
    test_flights = [
        {"icao24": "ae1234", "callsign": "REACH123", "squawk": "1234", "origin_country": "United States"},
        {"icao24": "43c5a8", "callsign": "RRR7742",  "squawk": "4532", "origin_country": "United Kingdom"},
        {"icao24": "3c4d22", "callsign": None,        "squawk": "0000", "origin_country": "Germany"},
        {"icao24": "4ca2c6", "callsign": "RYR4321",  "squawk": "2341", "origin_country": "Ireland"},
        {"icao24": "a12345", "callsign": "UPS1234",  "squawk": "5678", "origin_country": "United States"},
        {"icao24": "abc123", "callsign": "SAM001",   "squawk": "7700", "origin_country": "United States"},
    ]

    print("VigilHex - Aircraft Classifier Test")
    print("=" * 60)

    for flight in test_flights:
        result = classify_aircraft(flight)
        flag = "🚨" if result["priority_flag"] else "  "
        print(
            f"{flag} [{result['category']:<10}] "
            f"{result['icao24'].upper()} / "
            f"{result['callsign'] or 'NO_CALLSIGN':<12} "
            f"conf={result['category_confidence']:.2f} "
            f"squawk={result.get('special_squawk') or '-'}"
        )
```

Commit con messaggio:
```
feat: add aircraft classifier with military/state/commercial detection
