"""
In-memory mocks for the Stratum AI demos and tests.

DEMO MODE GUARD: these mocks are for owner testing ONLY. They refuse to
load when STRATUM_ENV=production — nothing fake ever runs in production.

Each mock implements the same interface the real connector would, so the
demo exercises the ACTUAL agent code paths — not a fake version of them.
"""
import os
from datetime import datetime, timedelta
from types import SimpleNamespace


def _guard() -> None:
    if os.getenv("STRATUM_ENV", "development") == "production":
        raise RuntimeError(
            "DEMOS/mocks are demo-only and are DISABLED when STRATUM_ENV=production. "
            "Run the real connectors (bring your own credentials) or set STRATUM_ENV=development."
        )


_guard()


# ---------------------------------------------------------------------------
# Fake LLM: returns canned JSON for known prompts, so demos run offline
# ---------------------------------------------------------------------------
class FakeLLM:
    """Rule-based stand-in for an LLM client (has .invoke() and .content)."""

    def invoke(self, prompt: str, **kwargs):
        return SimpleNamespace(content=self._answer(prompt))

    def _answer(self, prompt: str) -> str:
        p = prompt.lower()
        # only look at the lead's message, never the prompt schema itself
        message = p.split("message:", 1)[-1].split("lead metadata:", 1)[0]
        if "intent" in p and "buy|sell|rent" in p:  # lead qualifier profile
            # content-aware: mirrors the lead's own message so warm/cold
            # scenarios route correctly in the demos
            if "6 months" in message or "six months" in message:
                return ('{"intent":"buy","budget":420000,"area":"","timeline":"3-6mo",'
                        '"property_type":"house","financing":"need_mortgage",'
                        '"beds":3,"baths":2,"motivation":"planning ahead"}')
            if "rent" in message or "invest" in message:
                return ('{"intent":"invest","budget":300000,"area":"","timeline":"6mo+",'
                        '"property_type":"multi","financing":"unknown",'
                        '"beds":2,"baths":2,"motivation":""}')
            return ('{"intent":"buy","budget":650000,"area":"Maplewood","timeline":"asap",'
                    '"property_type":"house","financing":"preapproved","beds":3,"baths":2,'
                    '"motivation":"relocating for work"}')
        if "extract appointment details" in p:
            return '{"service":"cleaning","preferred_date":"2026-08-10","preferred_time":"10:00"}'
        if "classify the following document" in p:
            return '{"document_type":"carrier_invoice","confidence":0.95,"reason":"invoice header detected"}'
        if "extract structured fields from this carrier" in p:
            return ('{"invoice_number":"INV-88213","shipment_reference":"SH-1001","carrier":"FedEx",'
                    '"shipper":"Acme Parts Co","consignee":"BuildCo","origin":"Denver",'
                    '"destination":"Salt Lake City","amount":1250.0,"currency":"USD",'
                    '"date":"2026-07-28","weight_lbs":8420,"pieces":14,'
                    '"accessorials":["liftgate"],"fuel_surcharge":95.0,"payment_terms":"Net 30"}')
        return '{"status":"ok"}'


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
class MockCalendar:
    """Generates deterministic weekday availability; stores events in memory."""

    def __init__(self, start_hour: int = 9, end_hour: int = 17, busy_lunch: bool = True):
        self.events = []
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.busy_lunch = busy_lunch

    def get_free_slots(self, start, end, duration_min: int = 30, limit: int = 10) -> list[dict]:
        slots = []
        cursor = start.replace(minute=0, second=0, microsecond=0)
        while cursor < end and len(slots) < limit:
            if cursor.weekday() < 5 and self.start_hour <= cursor.hour < self.end_hour:
                if not (self.busy_lunch and cursor.hour == 12):
                    slots.append({
                        "start": cursor.isoformat(),
                        "end": (cursor + timedelta(minutes=duration_min)).isoformat(),
                    })
            cursor += timedelta(minutes=30)
        return slots

    def list_events(self, time_min=None, time_max=None) -> list[dict]:
        return list(self.events)

    def create_event(self, summary, start, end, description="", attendees=None) -> dict:
        event = {
            "id": f"evt-{len(self.events) + 1}",
            "summary": summary,
            "start": start.isoformat() if isinstance(start, datetime) else start,
            "end": end.isoformat() if isinstance(end, datetime) else end,
            "description": description,
            "attendees": attendees or [],
        }
        self.events.append(event)
        return event

    def cancel_event(self, event_id: str) -> None:
        self.events = [e for e in self.events if e.get("id") != event_id]


# ---------------------------------------------------------------------------
# Practice management system (clinic vertical)
# ---------------------------------------------------------------------------
class MockPMS:
    """Stores patients, appointments, insurance records in memory."""

    def __init__(self):
        self.patients: dict[str, dict] = {}
        self.appointments: list[dict] = []
        self.insurance_queue: list[dict] = []
        self.saved_insurance: dict[str, dict] = {}

    def upsert_patient(self, patient: dict) -> dict:
        pid = patient.get("id") or f"p-{len(self.patients) + 1}"
        patient["id"] = pid
        self.patients[pid] = patient
        return patient

    def get_patient(self, patient_id: str):
        return self.patients.get(patient_id)

    def find_patient_by_phone(self, phone: str):
        for p in self.patients.values():
            if p.get("phone") == phone:
                return p
        return None

    def create_appointment(self, patient_id=None, service="", start=None, end=None,
                           source="ai", **kwargs) -> dict:
        appointment = {
            "id": f"appt-{len(self.appointments) + 1}",
            "patient_id": patient_id,
            "service": service,
            "start": start,
            "end": end,
            "source": source,
        }
        self.appointments.append(appointment)
        return appointment

    def cancel_appointment(self, patient_id=None, start=None, **kwargs) -> None:
        self.appointments = [
            a for a in self.appointments
            if not (a.get("patient_id") == patient_id and (start is None or a.get("start") == start))
        ]

    def get_appointments(self, start=None, end=None) -> list[dict]:
        return list(self.appointments)

    def queue_insurance_verification(self, patient_id, data: dict) -> None:
        self.insurance_queue.append({"patient_id": patient_id, "data": data})

    def save_insurance(self, patient_id, data: dict) -> None:
        self.saved_insurance[patient_id] = data

    def get_follow_up_candidates(self, window_hours: int = 2) -> list[dict]:
        return []


# ---------------------------------------------------------------------------
# Communication mocks (SMS + email)
# ---------------------------------------------------------------------------
class MockComms:
    """Prints outbound SMS like Twilio would send them."""

    def __init__(self, silent: bool = False):
        self.sent: list[dict] = []
        self.silent = silent

    def send(self, to: str, body: str, **kwargs) -> dict:
        self.sent.append({"to": to, "body": body})
        if not self.silent:
            print(f"  📨 [SMS → {to}] {body}")
        return {"sid": f"SM{len(self.sent):04d}", "status": "sent", "to": to}


class MockEmailer:
    """Prints outbound email."""

    def __init__(self, silent: bool = False):
        self.sent: list[dict] = []
        self.silent = silent

    def send(self, to: str, subject: str, html=None, text=None, **kwargs) -> dict:
        self.sent.append({"to": to, "subject": subject})
        if not self.silent:
            print(f"  📧 [EMAIL → {to}] {subject}")
        return {"status": "sent", "to": to}


# ---------------------------------------------------------------------------
# CRM (real estate vertical)
# ---------------------------------------------------------------------------
class MockCRM:
    """Minimal in-memory CRM implementing the CRMInterface contract."""

    def __init__(self):
        self.contacts: list[dict] = []
        self.activities: list[dict] = []
        self.deals: list[dict] = []
        self._next = 1

    def find_contact(self, email=None, phone=None):
        for c in self.contacts:
            if email and c.get("email") == email:
                return c
            if phone and c.get("phone") == phone:
                return c
        return None

    def get_contact(self, contact_id: str):
        for c in self.contacts:
            if c.get("id") == contact_id:
                return c
        return None

    def create_contact(self, data: dict) -> str:
        contact = {"id": str(self._next), **data}
        self._next += 1
        self.contacts.append(contact)
        return contact["id"]

    def update_contact(self, contact_id: str, data: dict) -> None:
        for c in self.contacts:
            if c.get("id") == contact_id:
                c.update(data)

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        self.activities.append({"contact_id": contact_id, "type": activity_type, "note": note})

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        deal = {"id": f"deal-{len(self.deals) + 1}", "contact_id": contact_id,
                "title": title, "stage": stage, "value": value}
        self.deals.append(deal)
        return deal["id"]


# ---------------------------------------------------------------------------
# MLS (real estate vertical)
# ---------------------------------------------------------------------------
class MockMLS:
    """Static listing pool with filtering, like the real MLS connector."""

    LISTINGS = [
        {"mls_id": "M1001", "address": "412 Oakwood Lane", "price": 585000, "beds": 3,
         "baths": 2, "sqft": 2100, "area": "Maplewood", "property_type": "house",
         "url": "https://example.com/1", "photos": []},
        {"mls_id": "M1002", "address": "88 Riverside Dr, Apt 4B", "price": 420000, "beds": 2,
         "baths": 2, "sqft": 1250, "area": "Downtown", "property_type": "condo",
         "url": "https://example.com/2", "photos": []},
        {"mls_id": "M1003", "address": "7 Summit Court", "price": 760000, "beds": 4,
         "baths": 3, "sqft": 2950, "area": "Hillcrest", "property_type": "house",
         "url": "https://example.com/3", "photos": []},
        {"mls_id": "M1004", "address": "1509 Birchwood Ave", "price": 525000, "beds": 3,
         "baths": 1, "sqft": 1800, "area": "Maplewood", "property_type": "house",
         "url": "https://example.com/4", "photos": []},
        {"mls_id": "M1005", "address": "23 Marina Way", "price": 940000, "beds": 4,
         "baths": 4, "sqft": 2600, "area": "Waterfront", "property_type": "townhome",
         "url": "https://example.com/5", "photos": []},
    ]

    def search(self, max_price=None, area=None, property_type=None, beds=None,
               baths=None, limit=10) -> list[dict]:
        result = list(self.LISTINGS)
        if max_price:
            result = [l for l in result if l["price"] <= max_price]
        if beds:
            result = [l for l in result if l["beds"] >= beds]
        if baths:
            result = [l for l in result if l["baths"] >= baths]
        if property_type:
            result = [l for l in result if l["property_type"] == property_type]
        if area:
            result = [l for l in result if area.lower() in l["area"].lower()]
        return result[:limit]


# ---------------------------------------------------------------------------
# Logistics mocks: TMS/ledger, rate tables, accounting, insurance API
# ---------------------------------------------------------------------------
class MockTMS:
    """Shipment ledger + exceptions store, like a TMW-style TMS."""

    def __init__(self):
        now = datetime.now()
        self.shipments = {
            "SH-1001": {
                "id": "SH-1001", "reference": "SH-1001", "carrier": "FedEx",
                "origin": "Denver", "destination": "Salt Lake City",
                "equipment": "53ft", "authorized_accessorials": ["liftgate"],
                "cost": 1200.0, "status": "delivered", "on_time": True,
                "exceptions": [], "last_status": "delivered",
                "hours_since_last_scan": 0,
                "delivered_at": (now - timedelta(hours=72)).isoformat(),
                "pod_received": False,
                "carrier_email": "billing@fedex.example.com",
                "eta": (now + timedelta(hours=6)).isoformat(),
                "committed_delivery": (now + timedelta(hours=10)).isoformat(),
            },
            "SH-1002": {
                "id": "SH-1002", "reference": "SH-1002", "carrier": "UPS",
                "origin": "Chicago", "destination": "Omaha",
                "equipment": "48ft", "authorized_accessorials": [],
                "cost": 940.0, "status": "in_transit", "on_time": None,
                "exceptions": [], "last_status": "in_transit",
                "hours_since_last_scan": 31,
                "appointment_time": (now - timedelta(hours=5)).isoformat(),
                "carrier_email": "billing@ups.example.com",
            },
        }
        self.exceptions: list[dict] = []
        self.claims: list[dict] = []
        self._next_exc = 1

    def get_shipment(self, reference: str):
        return self.shipments.get(reference)

    def create_exception(self, shipment_id: str, exception: dict) -> None:
        exc = {"id": f"exc-{self._next_exc}", **exception}
        self._next_exc += 1
        self.exceptions.append(exc)
        shipment = self.shipments.get(shipment_id)
        if shipment is not None:
            shipment.setdefault("exceptions", []).append(exc)

    def mark_exception(self, exception_id: str, status: str) -> None:
        for exc in self.exceptions:
            if exc.get("id") == exception_id:
                exc["status"] = status

    def submit_claim(self, claim: dict) -> None:
        self.claims.append(claim)

    def shipments_in_period(self, period: str) -> list[dict]:
        return list(self.shipments.values())

    def exceptions_in_period(self, period: str) -> list[dict]:
        return list(self.exceptions)

    def spend_by_lane(self, period: str) -> list[dict]:
        return [{"lane": "Denver → Salt Lake City", "spend": 1200.0},
                {"lane": "Chicago → Omaha", "spend": 940.0}]

    def spend_by_mode(self, period: str) -> list[dict]:
        return [{"mode": "Truckload", "spend": 2140.0}]


class MockRateTables:
    """Contracted rates keyed by (carrier, origin, destination, equipment)."""

    def __init__(self):
        self.rates = {
            ("FedEx", "Denver", "Salt Lake City", "53ft"): {"total": 1200.0},
            ("UPS", "Chicago", "Omaha", "48ft"): {"total": 900.0},
        }

    def get_rate(self, carrier: str, lane: tuple, equipment=None):
        return self.rates.get((carrier, lane[0], lane[1], equipment))


class MockAccounting:
    """Records approvals, holds, disputes and credit requests."""

    def __init__(self):
        self.approved: list[str] = []
        self.held: list[dict] = []
        self.disputes: list[dict] = []
        self.credits: list[dict] = []

    def mark_ready_to_pay(self, invoice_id, reference="") -> None:
        self.approved.append(invoice_id)

    def hold_payment(self, invoice_id, reasons=None) -> None:
        self.held.append({"id": invoice_id, "reasons": reasons or []})

    def submit_dispute(self, dispute: dict) -> None:
        self.disputes.append(dispute)

    def request_credit(self, credit: dict) -> None:
        self.credits.append(credit)

    def invoices_in_period(self, period: str) -> list[dict]:
        return [
            {"id": "INV-1", "amount": 1208.0, "status": "approved", "days_to_pay": 12},
            {"id": "INV-2", "amount": 1250.0, "status": "held", "days_to_pay": 5},
        ]


class MockInsuranceAPI:
    """Insurance eligibility stub (mirrors InsuranceVerificationAPI)."""

    def verify(self, carrier: str, member_id: str, plan_name: str, dob: str) -> dict:
        return {
            "status": "active",
            "plan": plan_name or f"{carrier} PPO",
            "effective_date": "2026-01-01",
            "deductible": 50.0,
            "copay_cleaning": 0.0,
            "copay_exam": 25.0,
            "annual_maximum": 1500.0,
            "notes": "MOCK DATA — demo only",
        }
