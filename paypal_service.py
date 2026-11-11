import os
import requests
from dotenv import load_dotenv

load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


def get_paypal_access_token():
    """Generates an OAuth2 access token from PayPal Sandbox."""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        url, auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET), headers=headers, data=data
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"PayPal Auth Failed: {response.text}")


def execute_sandbox_resolution(amount: str = "180.00", currency: str = "USD"):
    """
    Creates a verified order in the PayPal Sandbox to demonstrate
    real-time automated dispute payout/settlement execution.
    """
    token = get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": "DISPUTE-REFUND-SETTLEMENT",
                "description": "PayPal ResolveAI Approved Claim Settlement",
                "amount": {"currency_code": currency, "value": amount},
            }
        ],
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        data = response.json()
        return {
            "success": True,
            "order_id": data.get("id"),
            "status": data.get("status"),
            "links": data.get("links"),
        }
    else:
        return {"success": False, "error": response.text}
