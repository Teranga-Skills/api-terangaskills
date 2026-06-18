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
                        "text": """
Tu es un moteur d'extraction de données spécialisé dans les documents administratifs des collectivités territoriales du Sénégal.

Analyse le document fourni et extrais uniquement les informations suivantes :

- nom
- prenom
- date_naissance
- numero_identification

Règles d'extraction :

1. Le nom et le prénom doivent être retournés tels qu'ils apparaissent dans le document, sans modification.
2. Pour la date de naissance :
   - Rechercher les mentions telles que « Né(e) le », « Date de naissance », ou toute formulation équivalente.
   - Convertir systématiquement la date au format JJ/MM/AAAA.
3. Pour le numéro d'identification :
   - Rechercher tout identifiant administratif pertinent (CNI, acte, passeport, etc.).
   - Le numéro doit toujours commencer par un chiffre (pas de lettre en tête).
   - Retirer tout préfixe alphabétique (ex. « SN », « P », « TS ») et ne conserver que la partie numérique.
   - Conserver tirets ou chiffres tels qu'affichés si possible.
4. Si une information est absente, illisible ou non identifiable avec certitude, retourner null.
5. Ne jamais inventer ni déduire une valeur.
6. Ignorer les informations concernant les parents, témoins, agents municipaux, maires ou officiers d'état civil.
7. Si plusieurs personnes sont mentionnées, extraire uniquement les informations de la personne principale concernée par le document.

Retourne uniquement un JSON valide sans texte supplémentaire :

{
  "nom": "string|null",
  "prenom": "string|null",
  "date_naissance": "JJ/MM/AAAA|null",
  "numero_identification": "string|null"
}
"""
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
    print(response.json())

    return response.json()

