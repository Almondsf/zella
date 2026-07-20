import requests
from django.conf import settings

PAYSTACK_BASE_URL = 'https://api.paystack.co'

def initialize_payment(email, amount, reference):
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'email': email,
        'amount': int(amount) * 100,  # convert to kobo
        'reference': reference
    }
    response = requests.post(
        f'{PAYSTACK_BASE_URL}/transaction/initialize',
        json=payload,
        headers=headers
    )
    return response.json()