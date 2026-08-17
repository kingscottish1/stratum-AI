"""
Sage Intacct connector — AP automation (bills, approvals, payments).

Env vars: INTACCT_SENDER_ID, INTACCT_SENDER_PASSWORD, INTACCT_COMPANY_ID,
          INTACCT_USER_ID, INTACCT_USER_PASSWORD
"""
import os
import xml.etree.ElementTree as ET
from typing import Optional

import requests


class SageIntacctConnector:
    ENDPOINT = "https://api.intacct.com/ia/xml/xmlgw.phtml"

    def __init__(self, sender_id: Optional[str] = None, company_id: Optional[str] = None,
                 user_id: Optional[str] = None, user_password: Optional[str] = None):
        self.sender_id = sender_id or os.getenv("INTACCT_SENDER_ID", "")
        self.company_id = company_id or os.getenv("INTACCT_COMPANY_ID", "")
        self.user_id = user_id or os.getenv("INTACCT_USER_ID", "")
        self.user_password = user_password or os.getenv("INTACCT_USER_PASSWORD", "")

    def _auth_xml(self) -> str:
        return (
            f"<control><senderid>{self.sender_id}</senderid>"
            f"<password>CHANGE_ME</password>"
            f"<controlid>stratum-{__import__('uuid').uuid4().hex[:8]}</controlid>"
            f"<uniqueid>false</uniqueid><dtdversion>3.0</dtdversion></control>"
            f"<operation><authentication>"
            f"<login><userid>{self.user_id}</userid>"
            f"<companyid>{self.company_id}</companyid>"
            f"<password>{self.user_password}</password></login>"
            f"</authentication></operation>"
        )

    def _call(self, function_xml: str) -> ET.Element:
        payload = f"<?xml version='1.0'?><request>{self._auth_xml()}<content><function>{function_xml}</function></content></request>"
        resp = requests.post(self.ENDPOINT, data={"xmlrequest": payload}, timeout=30)
        resp.raise_for_status()
        return ET.fromstring(resp.text)

    def mark_ready_to_pay(self, bill_id: str, reference: str = "") -> None:
        # update bill status via update_approvebill / apbill
        self._call(f"<update_approvebill><key>{bill_id}</key></update_approvebill>")

    def hold_payment(self, bill_id: str, reasons: list[str]) -> None:
        self._call(
            f"<update_apbill><key>{bill_id}</key><update>"
            f"<state>DRAFT</state><memo>HELD BY AI: {'; '.join(reasons)}</memo>"
            f"</update></update_apbill>"
        )

    def request_credit(self, credit: dict) -> None:
        self._call(
            f"<create_vendorcredit><vendorcredit>"
            f"<vendorid>{credit.get('vendor_id', '')}</vendorid>"
            f"<billno>{credit.get('shipment', '')}</billno>"
            f"<totalamount>{credit.get('credit_amount', 0)}</totalamount>"
            f"</vendorcredit></create_vendorcredit>"
        )
