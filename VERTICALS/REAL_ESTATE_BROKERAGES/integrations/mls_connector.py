"""
MLS connector — abstract over any MLS provider (ResoWebAPI, Bridge, local IDX).

Env vars: MLS_PROVIDER (resowebapi|bridge|other), MLS_API_KEY, MLS_API_SECRET,
          MLS_ENDPOINT
"""
import os
from typing import Optional

import requests


class MLSConnector:
    """Minimal MLS search surface used by the property matcher."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("MLS_PROVIDER", "resowebapi")
        self.api_key = os.getenv("MLS_API_KEY", "")
        self.api_secret = os.getenv("MLS_API_SECRET", "")
        self.endpoint = os.getenv("MLS_ENDPOINT", "")

    def search(
        self,
        max_price: Optional[float] = None,
        area: Optional[str] = None,
        property_type: Optional[str] = None,
        beds: Optional[int] = None,
        baths: Optional[int] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Return listings normalized to:
        {mls_id, address, price, beds, baths, sqft, area, property_type,
         url, photos[]}
        """
        if self.provider == "mock":
            return self._mock_search(max_price, area, property_type, beds, baths, limit)
        raise NotImplementedError(
            f"Implement MLS search for provider={self.provider} "
            "(RESO Web API: POST /Property with OData filter)"
        )

    def _mock_search(self, max_price, area, property_type, beds, baths, limit) -> list[dict]:
        """Development stub returning deterministic fake listings."""
        base = [
            {"mls_id": "M1001", "address": "412 Oakwood Lane", "price": 585000,
             "beds": 3, "baths": 2, "sqft": 2100, "area": "Maplewood",
             "property_type": "house", "url": "https://example.com/1", "photos": []},
            {"mls_id": "M1002", "address": "88 Riverside Dr, Apt 4B", "price": 420000,
             "beds": 2, "baths": 2, "sqft": 1250, "area": "Downtown",
             "property_type": "condo", "url": "https://example.com/2", "photos": []},
            {"mls_id": "M1003", "address": "7 Summit Court", "price": 760000,
             "beds": 4, "baths": 3, "sqft": 2950, "area": "Hillcrest",
             "property_type": "house", "url": "https://example.com/3", "photos": []},
            {"mls_id": "M1004", "address": "1509 Birchwood Ave", "price": 525000,
             "beds": 3, "baths": 1, "sqft": 1800, "area": "Maplewood",
             "property_type": "house", "url": "https://example.com/4", "photos": []},
            {"mls_id": "M1005", "address": "23 Marina Way", "price": 940000,
             "beds": 4, "baths": 4, "sqft": 2600, "area": "Waterfront",
             "property_type": "townhome", "url": "https://example.com/5", "photos": []},
        ]
        result = base
        if max_price:
            result = [l for l in result if l["price"] <= max_price]
        if beds:
            result = [l for l in result if l["beds"] >= beds]
        if property_type:
            result = [l for l in result if l["property_type"] == property_type]
        if area:
            result = [l for l in result if area.lower() in l["area"].lower()]
        return result[:limit]
