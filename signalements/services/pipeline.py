import json
import re
from signalements.services.ocr import ocr_extract
from signalements.services.identification_utils import (
    find_registre_by_identification,
    sanitize_identification,
)
from signalements.models import AnalyseIA


def _matched_data_from_registre(entry):
    return {
        "nom": entry.nom,
        "prenom": entry.prenom,
        "date_naissance": entry.date_naissance.strftime("%d/%m/%Y") if entry.date_naissance else None,
        "numero_identification": entry.numero_identification,
        "type_acte": entry.type_acte,
        "centre": entry.centre.nom if entry.centre else None,
    }


def run_pipeline(file, user):

    # 1. OCR
    ocr_result = ocr_extract(file)

    data = ocr_result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

    extracted = {
        "nom": "UNKNOWN",
        "prenom": "UNKNOWN",
        "date_naissance": "UNKNOWN",
        "numero_identification": "UNKNOWN",
    }

    if data:
        try:
            cleaned = data.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
            parsed = json.loads(cleaned.strip())

            extracted["nom"] = str(parsed.get("nom") or parsed.get("nom_famille") or "UNKNOWN").upper().strip()
            extracted["prenom"] = str(parsed.get("prenom") or parsed.get("prenoms") or "UNKNOWN").strip()
            extracted["date_naissance"] = str(
                parsed.get("date_naissance") or parsed.get("dateNaissance") or "UNKNOWN"
            ).strip()
            raw_numero = str(
                parsed.get("numero_identification")
                or parsed.get("numeroDocument")
                or parsed.get("numero_acte")
                or parsed.get("numero")
                or "UNKNOWN"
            ).strip()
            extracted["numero_identification"] = sanitize_identification(raw_numero) or "UNKNOWN"
        except Exception:
            pass

    # 2. Comparaison avec le registre officiel en base de données
    matched = find_registre_by_identification(extracted["numero_identification"])
    similarity = 100 if matched else 0

    # 3. Logique fraude
    fraud_score = 0
    decision = "VALID"
    risk_level = "LOW"
    matched_data = None

    if matched:
        ext_nom = extracted["nom"].upper().replace(" ", "")
        ext_prenom = extracted["prenom"].upper().replace(" ", "")

        base_nom = matched.nom.upper().replace(" ", "")
        base_prenom = matched.prenom.upper().replace(" ", "")

        if ext_nom == base_nom and ext_prenom == base_prenom:
            fraud_score = 15
            decision = "VALID"
            risk_level = "LOW"
        else:
            fraud_score = 50
            decision = "SUSPECT"
            risk_level = "MEDIUM"

        matched_data = _matched_data_from_registre(matched)
    else:
        fraud_score = 95
        decision = "FRAUD"
        risk_level = "HIGH"

    analyse = AnalyseIA.objects.create(
        acte=None,
        ocr_text=str(ocr_result),
        extracted_data=extracted,
        matched_acte=None,
        matched_registre=matched,
        similarity_score=similarity,
        fraud_score=fraud_score,
        risk_level=risk_level,
        decision=decision,
        model_used="openai/gpt-4o-mini",
    )

    return {
        "analyse_id": str(analyse.id),
        "decision": decision,
        "fraud_score": fraud_score,
        "similarity_score": similarity,
        "matched": bool(matched),
        "extracted_data": extracted,
        "matched_data": matched_data,
    }
