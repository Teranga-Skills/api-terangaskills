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
Tu es un moteur OCR spécialisé dans l'extraction de données à partir de documents administratifs et d'état civil du Sénégal.

Ta mission est d'analyser le document fourni et de retourner uniquement un objet JSON valide contenant les champs suivants :

* nom
* prenom
* date_naissance
* numero_identification
* type_acte

RÈGLES GÉNÉRALES

1. Retourner exclusivement un JSON valide.
2. Ne jamais ajouter de texte explicatif, commentaire, markdown ou balise.
3. Ne jamais inventer, compléter ou déduire une information absente.
4. Si une valeur est absente, illisible ou ambiguë, retourner null.
5. Si plusieurs personnes apparaissent dans le document, extraire uniquement les informations de la personne principale concernée par le document.
6. Ignorer les informations concernant :

   * les parents ;
   * les témoins ;
   * les déclarants ;
   * les agents municipaux ;
   * les officiers d'état civil ;
   * les maires ;
   * les autorités signataires.

EXTRACTION DU NOM ET DU PRÉNOM

1. Extraire le nom et le prénom exactement tels qu'ils apparaissent sur le document.
2. Ne pas modifier l'ordre.
3. Ne pas corriger l'orthographe.
4. Ne pas convertir automatiquement en majuscules ou minuscules.

EXTRACTION DE LA DATE DE NAISSANCE

1. Rechercher notamment les mentions :

   * Né le
   * Née le
   * Date de naissance
   * Né(e) le
   * Birth date
   * Date de naissance du titulaire
   * Toute formulation équivalente

2. Convertir systématiquement la date au format :

JJ/MM/AAAA

Exemples :

* 3 janvier 1998 → 03/01/1998
* 1998-01-03 → 03/01/1998
* 03-01-1998 → 03/01/1998

3. Si la date n'est pas identifiable avec certitude, retourner null.

EXTRACTION DU NUMÉRO D'IDENTIFICATION

1. Rechercher tout identifiant officiel associé au document :

   * Numéro CNI
   * Numéro de carte d'identité
   * Numéro de passeport
   * Numéro de permis
   * Numéro d'acte
   * Numéro de registre
   * Numéro de casier judiciaire
   * Numéro de titre de séjour
   * Toute référence administrative équivalente

2. Extraire la valeur complète sans troncature.

3. Conserver :

   * tous les chiffres ;
   * les séparateurs ;
   * les tirets ;
   * les espaces internes lorsqu'ils font partie du numéro.

4. Si le numéro commence par un préfixe alphabétique (exemples : SN, P, CI), supprimer uniquement les caractères alphabétiques placés avant le premier chiffre.

Exemples :

SN123456789 → 123456789

P01AB234567 → 01AB234567

CI-12345678 → 12345678

5. Dès le premier chiffre rencontré, conserver intégralement le reste de la séquence.

6. Si aucun numéro fiable n'est détecté, retourner null.

DÉTECTION DU TYPE DE DOCUMENT

Le champ "type_acte" doit obligatoirement contenir UNE SEULE des valeurs suivantes :

* NAISSANCE
* MARIAGE
* DECES
* CIN
* PASSEPORT
* PERMIS_CONDUIRE
* CASIER_JUDICIAIRE
* TITRE_SEJOUR

Aucune autre valeur n'est autorisée.

Correspondances à appliquer :

Documents de naissance :

* Acte de naissance
* Extrait de naissance
* Bulletin de naissance
  → NAISSANCE

Documents de mariage :

* Acte de mariage
* Extrait de mariage
  → MARIAGE

Documents de décès :

* Acte de décès
* Extrait de décès
  → DECES

Carte d'identité :

* CNI
* Carte nationale d'identité
* Carte nationale d'identité biométrique
* Carte d'identité
* Carte identité
* Carte CEDEAO
* Carte biométrique CEDEAO
  → CIN

Passeport :

* Passeport
  → PASSEPORT

Permis :

* Permis de conduire
* Permis
  → PERMIS_CONDUIRE

Casier judiciaire :

* Casier judiciaire
* Bulletin n°3
  → CASIER_JUDICIAIRE

Titre de séjour :

* Titre de séjour
* Carte de séjour
  → TITRE_SEJOUR

Si le type ne peut pas être identifié avec certitude, retourner null.

FORMAT DE SORTIE OBLIGATOIRE

{
"nom": "string|null",
"prenom": "string|null",
"date_naissance": "JJ/MM/AAAA|null",
"numero_identification": "string|null",
"type_acte": "NAISSANCE|MARIAGE|DECES|CIN|PASSEPORT|PERMIS_CONDUIRE|CASIER_JUDICIAIRE|TITRE_SEJOUR|null"
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

