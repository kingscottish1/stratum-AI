"""
Zillow API connector (Bridge/Zillow API) — property data and lead events.

Env vars: ZILLOW_API_KEY, ZILLOW_API_EMAIL
"""
import os
from typing import Optional

import requests

ZILLOW_BASE = "https://api.bridgedataoutput.com/api/v2"


class ZillowAPIConnector:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ZILLOW_API_KEY", "")

    def search(self, **filters) -> list[dict]:
        """Search listings. Filters: address, city, state, zipcode, minPrice, maxPrice, beds, baths."""
        params = {"access_token": self.api_key, "limit": 25}
        params.update({k: v for k, v in filters.items() if v is not None})
        resp = requests.get(f"{ZILLOW_BASE}/zestimates", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("bundle", [])

    def get_property(self, zpid: str) -> Optional[dict]:
        resp = requests.get(f"{ZILLOW_BASE}/zestimates/{zpid}",
                            params={"access_token": self.api_key}, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def lead_events(self, since: str = "") -> list[dict]:
        """Pull lead events from Zillow (requires lead feeds enabled)."""
        # TODO: implement per Zillow's lead API contract
        return []
