import requests
import base64
import os


def ocr_extract(file):

    # Détecter le type d'entrée (fichier Django, chemin local ou base64 direct)
    if isinstance(file, str):
        if len(file) > 1000 or file.startswith("data:"):
            # Déjà encodé en base64
            if "," in file:
                encoded = file.split(",")[1]
            else:
                encoded = file
        else:
            # Chemin local vers le fichier
            with open(file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
    else:
        # Fichier Django / objet file-like
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
                "content": "Tu es un OCR intelligent de documents d'état civil sénégalais. Analyse l'image et retourne uniquement un objet JSON contenant les champs extraits sans aucun autre texte."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extrais les champs suivants sous forme de JSON : nom, prenom, date_naissance (au format JJ/MM/AAAA), numero_identification."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded}"
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()