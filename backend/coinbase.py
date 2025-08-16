import requests
import os
import json

def send_usdc(amount: float, user_wallet: str):
    """Invia USDC da Coinbase a un wallet utente"""
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_WALLET_ID = os.getenv("COINBASE_WALLET_ID")
    
    url = "https://api.coinbase.com/v2/accounts/{}/transactions".format(COINBASE_WALLET_ID)
    headers = {
        "Authorization": f"Bearer {COINBASE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "send",
        "to": user_wallet,
        "amount": str(amount),
        "currency": "USDC",
        "description": "Lisprocoin Game Payout"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            tx_data = response.json()
            return True, "Success", tx_data['data']['id']
        return False, f"Error {response.status_code}: {response.text}", None
    except Exception as e:
        return False, str(e), None

def verify_coinbase_payment(tx_hash: str):
    """Verifica una transazione Coinbase (semplificata)"""
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    url = f"https://api.coinbase.com/v2/transactions/{tx_hash}"
    headers = {"Authorization": f"Bearer {COINBASE_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tx_data = response.json()
            return tx_data['data']['status'] == 'completed'
        return False
    except:
        return False
