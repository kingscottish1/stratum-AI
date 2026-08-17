"""
Microsoft Outlook / Exchange Online connector via Microsoft Graph.

Env vars required:
  AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, OUTLOOK_USER_ID
"""
import os
from datetime import datetime
from typing import Optional

import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class OutlookConnector:
    def __init__(self, user_id: Optional[str] = None):
        self.tenant = os.getenv("AZURE_TENANT_ID", "")
        self.client_id = os.getenv("AZURE_CLIENT_ID", "")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
        self.user_id = user_id or os.getenv("OUTLOOK_USER_ID", "me")
        self._token: Optional[str] = None

    def _auth(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._auth()}"}

    def list_events(self, start: datetime, end: datetime) -> list[dict]:
        url = f"{GRAPH_BASE}/users/{self.user_id}/calendar/events"
        params = {
            "$filter": f"start/dateTime ge '{start.isoformat()}' and end/dateTime le '{end.isoformat()}'",
            "$select": "id,subject,start,end",
        }
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def create_event(self, subject: str, start: datetime, end: datetime, body: str = "") -> dict:
        url = f"{GRAPH_BASE}/users/{self.user_id}/calendar/events"
        payload = {
            "subject": subject,
            "body": {"contentType": "text", "content": body},
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
