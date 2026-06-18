import json
import re
from signalements.services.ocr import ocr_extract
from signalements.models import AnalyseIA, ActeEtatCivil
from django.db.models import Q


def run_pipeline(file, user):

    # 1. OCR
    ocr_result = ocr_extract(file)

    data = ocr_result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

    # Parser le JSON extrait par l'OCR
    extracted = {
        "nom": "UNKNOWN",
        "prenom": "UNKNOWN",
        "date_naissance": "UNKNOWN",
        "numero_identification": "UNKNOWN"
    }

    if data:
        try:
            cleaned = data.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
            parsed = json.loads(cleaned.strip())
            
            # Récupérer les données avec fallbacks
            extracted["nom"] = str(parsed.get("nom") or parsed.get("nom_famille") or "UNKNOWN").upper().strip()
            extracted["prenom"] = str(parsed.get("prenom") or parsed.get("prenoms") or "UNKNOWN").strip()
            extracted["date_naissance"] = str(parsed.get("date_naissance") or parsed.get("dateNaissance") or "UNKNOWN").strip()
            extracted["numero_identification"] = str(parsed.get("numero_identification") or parsed.get("numeroDocument") or parsed.get("numero_acte") or parsed.get("numero") or "UNKNOWN").strip()
        except Exception:
            pass

    # 2. MATCH BASE EXISTANTE
    matched = None
    similarity = 0

    if extracted["numero_identification"] != "UNKNOWN":
        try:
            matched = ActeEtatCivil.objects.select_related("citoyen", "centre").get(
                citoyen__numero_identification=extracted["numero_identification"]
            )
            similarity = 100
        except ActeEtatCivil.DoesNotExist:
            matched = None

    # 3. LOGIQUE FRAUDE DÉTAILLÉE
    fraud_score = 0
    decision = "VALID"
    risk_level = "LOW"
    matched_data = None

    if matched:
        # Normalisation pour la comparaison
        ext_nom = extracted["nom"].upper().replace(" ", "")
        ext_prenom = extracted["prenom"].upper().replace(" ", "")
        
        base_nom = matched.citoyen.nom.upper().replace(" ", "")
        base_prenom = matched.citoyen.prenom.upper().replace(" ", "")

        if ext_nom == base_nom and ext_prenom == base_prenom:
            # CAS 2 : ID existe, nom et prénom correspondent exactement
            fraud_score = 15
            decision = "VALID"
            risk_level = "LOW"
        else:
            # CAS 3 : ID existe, mais nom et/ou prénom diffèrent
            fraud_score = 50
            decision = "SUSPECT"
            risk_level = "MEDIUM"

        # Préparer les données de comparaison
        matched_data = {
            "nom": matched.citoyen.nom,
            "prenom": matched.citoyen.prenom,
            "date_naissance": matched.citoyen.date_naissance.strftime("%d/%m/%Y") if matched.citoyen.date_naissance else None,
            "numero_identification": matched.citoyen.numero_identification,
            "type_acte": matched.type_acte,
            "centre": matched.centre.nom if matched.centre else None,
        }
    else:
        # CAS 1 : ID n'existe pas du tout en base de données
        fraud_score = 95
        decision = "FRAUD"
        risk_level = "HIGH"

    # 4. SAVE ANALYSE
    analyse = AnalyseIA.objects.create(
        acte=matched if matched else None,
        ocr_text=str(ocr_result),
        extracted_data=extracted,
        matched_acte=matched,
        similarity_score=similarity,
        fraud_score=fraud_score,
        risk_level=risk_level,
        decision=decision,
        model_used="openai/gpt-4o-mini"
    )

    return {
        "analyse_id": str(analyse.id),
        "decision": decision,
        "fraud_score": fraud_score,
        "similarity_score": similarity,
        "matched": bool(matched),
        "extracted_data": extracted,
        "matched_data": matched_data
    }