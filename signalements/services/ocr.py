import requests
import base64
import os


def ocr_extract(file):

    encoded = base64.b64encode(file.read()).decode()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un OCR. Retourne uniquement du JSON."
            },
            {
                "role": "user",
                "content": f"""
Extraire :
- nom
- prenom
- date_naissance
- numero_identification

IMAGE:
{encoded}
"""
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()