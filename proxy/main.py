"""
VigilHex Proxy Server
Fetches ADS-B data server-side to bypass CORS restrictions.
Deploy free on Render.com
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from datetime import datetime, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

OPENSKY_URL = "https://opensky-network.org/api/states/all"
cache = {"data": None, "ts": 0}
CACHE_SEC = 55

@app.get("/")
async def root():
    return {"status": "VigilHex proxy online", "time": datetime.now(timezone.utc).isoformat()}

@app.get("/flights")
async def get_flights():
    now = datetime.now(timezone.utc).timestamp()
    if cache["data"] and (now - cache["ts"]) < CACHE_SEC:
        return cache["data"]
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                OPENSKY_URL,
                headers={"User-Agent": "VigilHex/0.1"}
            )
            r.raise_for_status()
            data = r.json()
            cache["data"] = data
            cache["ts"] = now
            return data
    except Exception as e:
        if cache["data"]:
            return cache["data"]
        return {"states": [], "error": str(e)}
```

Commit: `feat: add proxy server for CORS bypass`

---

## FILE 2 — Crea `proxy/requirements.txt`

Nome: `proxy/requirements.txt`
```
fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0
