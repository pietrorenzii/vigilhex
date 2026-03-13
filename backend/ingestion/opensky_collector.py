"""
VigilHex - OpenSky Network Collector
Fetches real-time flight data from OpenSky Network public API.
No API key required for basic access.
Rate limit: 1 request / 10 seconds (anonymous)
"""

import requests
import logging
import time
from datetime import datetime, timezone
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vigilhex.opensky")

# OpenSky API endpoint
OPENSKY_URL = "https://opensky-network.org/api/states/all"

# State vector field positions (OpenSky API docs)
FIELDS = [
    "icao24",        # 0  - Unique ICAO hex identifier
    "callsign",      # 1  - Aircraft callsign
    "origin_country",# 2  - Country of registration
    "time_position", # 3  - Last position update (unix)
    "last_contact",  # 4  - Last contact with receiver (unix)
    "longitude",     # 5  - WGS-84 longitude
    "latitude",      # 6  - WGS-84 latitude
    "baro_altitude", # 7  - Barometric altitude (meters)
    "on_ground",     # 8  - True if aircraft is on ground
    "velocity",      # 9  - Ground speed (m/s)
    "true_track",    # 10 - True track (degrees, 0=North)
    "vertical_rate", # 11 - Vertical rate (m/s)
    "sensors",       # 12 - IDs of receivers
    "geo_altitude",  # 13 - Geometric altitude (meters)
    "squawk",        # 14 - Transponder squawk code
    "spi",           # 15 - Special purpose indicator
    "position_source"# 16 - 0=ADS-B, 1=ASTERIX, 2=MLAT
]


def fetch_all_flights(
    bbox: Optional[tuple] = None,
    timeout: int = 15
) -> list[dict]:
    """
    Fetch all current flight states from OpenSky Network.

    Args:
        bbox: Optional bounding box (min_lat, max_lat, min_lon, max_lon)
              None = worldwide
        timeout: HTTP request timeout in seconds

    Returns:
        List of flight dictionaries, empty list on error
    """
    params = {}
    if bbox:
        min_lat, max_lat, min_lon, max_lon = bbox
        params = {
            "lamin": min_lat,
            "lamax": max_lat,
            "lomin": min_lon,
            "lomax": max_lon
        }

    try:
        logger.info(f"Fetching flights from OpenSky (bbox={bbox or 'WORLDWIDE'})")
        start = time.time()

        response = requests.get(
            OPENSKY_URL,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "VigilHex/0.1 (github.com/pietrorenzii/vigilhex)"}
        )
        response.raise_for_status()

        data = response.json()
        elapsed = time.time() - start

        if not data or "states" not in data or data["states"] is None:
            logger.warning("OpenSky returned empty response")
            return []

        flights = []
        for state in data["states"]:
            flight = _parse_state_vector(state)
            if flight:
                flights.append(flight)

        logger.info(
            f"Fetched {len(flights)} flights in {elapsed:.2f}s "
            f"(timestamp: {data.get('time', 'unknown')})"
        )
        return flights

    except requests.exceptions.Timeout:
        logger.error("OpenSky request timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to OpenSky API")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"OpenSky HTTP error: {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching OpenSky data: {e}")
        return []


def _parse_state_vector(state: list) -> Optional[dict]:
    """
    Parse a raw OpenSky state vector into a clean flight dict.

    Args:
        state: Raw list from OpenSky API

    Returns:
        Parsed flight dict or None if invalid
    """
    try:
        # Skip aircraft with no position
        if state[5] is None or state[6] is None:
            return None

        # Convert m/s to knots (1 m/s = 1.94384 knots)
        velocity_ms = state[9]
        velocity_kts = round(velocity_ms * 1.94384, 1) if velocity_ms else None

        # Convert meters to feet (1 m = 3.28084 ft)
        baro_alt_m = state[7]
        baro_alt_ft = round(baro_alt_m * 3.28084) if baro_alt_m else None

        geo_alt_m = state[13]
        geo_alt_ft = round(geo_alt_m * 3.28084) if geo_alt_m else None

        # Calculate transponder status
        last_contact = state[4]
        now = int(datetime.now(timezone.utc).timestamp())
        transponder_silent_seconds = (now - last_contact) if last_contact else None

        callsign = state[1]
        clean_callsign = callsign.strip() if callsign else None

        return {
            # Identity
            "icao24": state[0],
            "callsign": clean_callsign,
            "origin_country": state[2],
            "squawk": state[14],

            # Position
            "latitude": state[6],
            "longitude": state[5],
            "baro_altitude_ft": baro_alt_ft,
            "geo_altitude_ft": geo_alt_ft,
            "on_ground": state[8],

            # Movement
            "velocity_kts": velocity_kts,
            "true_track_deg": state[10],
            "vertical_rate_fpm": round(state[11] * 196.85) if state[11] else None,

            # Signal
            "last_contact_unix": last_contact,
            "time_position_unix": state[3],
            "transponder_silent_sec": transponder_silent_seconds,
            "position_source": state[16],
            "spi": state[15],

            # Metadata
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except (IndexError, TypeError) as e:
        logger.debug(f"Failed to parse state vector: {e}")
        return None


def fetch_europe_flights() -> list[dict]:
    """Fetch flights over Europe — NATO/EU priority zone."""
    return fetch_all_flights(bbox=(35.0, 72.0, -15.0, 45.0))


def fetch_mediterranean_flights() -> list[dict]:
    """Fetch flights over Mediterranean Sea."""
    return fetch_all_flights(bbox=(30.0, 47.0, -5.0, 40.0))


def fetch_baltic_black_sea_flights() -> list[dict]:
    """Fetch flights over Baltic and Black Sea — high priority zones."""
    return fetch_all_flights(bbox=(40.0, 65.0, 10.0, 45.0))


# ── Quick test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("VigilHex - OpenSky Collector Test")
    print("=" * 50)

    flights = fetch_europe_flights()

    if flights:
        print(f"\nTotal flights over Europe: {len(flights)}")
        print("\nSample flight:")
        sample = flights[0]
        for k, v in sample.items():
            print(f"  {k}: {v}")

        # Show aircraft with no callsign (suspicious)
        no_callsign = [f for f in flights if not f["callsign"]]
        print(f"\nAircraft with no callsign: {len(no_callsign)}")

        # Show aircraft with transponder silent > 60s
        silent = [
            f for f in flights
            if f["transponder_silent_sec"] and f["transponder_silent_sec"] > 60
        ]
        print(f"Aircraft transponder silent >60s: {len(silent)}")
    else:
        print("No flights fetched — check connection")
```
