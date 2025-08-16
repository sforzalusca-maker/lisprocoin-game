import requests
import os

COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_WALLET_ID = os.getenv("COINBASE_WALLET_ID")

def send_usdc(from_wallet, amount):
    url = f"https://api.coinbase.com/v2/accounts/{from_wallet}/transactions"
    headers = {
        "Authorization": f"Bearer {COINBASE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "to": COINBASE_WALLET_ID,
        "amount": str(amount),
        "currency": "USDC",
        "type": "send"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 201
