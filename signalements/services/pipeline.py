from signalements.services.ocr import ocr_extract
from signalements.models import AnalyseIA, ActeEtatCivil
from django.db.models import Q


def run_pipeline(file, user):

    # 1. OCR
    ocr_result = ocr_extract(file)

    data = ocr_result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

    # ici simplifié (dans vrai hackathon tu parseras JSON)
    extracted = {
        "nom": "UNKNOWN",
        "prenom": "UNKNOWN",
        "date_naissance": "UNKNOWN",
        "numero_identification": "UNKNOWN"
    }

    # 2. MATCH BASE EXISTANTE
    matched = None
    similarity = 0

    if extracted["numero_identification"] != "UNKNOWN":

        try:
            matched = ActeEtatCivil.objects.get(
                citoyen__numero_identification=extracted["numero_identification"]
            )
            similarity = 100
        except ActeEtatCivil.DoesNotExist:
            matched = None

    # 3. LOGIQUE FRAUDE SIMPLE
    fraud_score = 0
    decision = "VALID"

    if matched:

        if (
            extracted["nom"] != matched.citoyen.nom or
            extracted["prenom"] != matched.citoyen.prenom
        ):
            fraud_score = 95
            decision = "FRAUD"
        else:
            fraud_score = 20
            decision = "VALID"

    # 4. SAVE ANALYSE
    analyse = AnalyseIA.objects.create(
        acte=matched if matched else None,
        ocr_text=str(ocr_result),
        extracted_data=extracted,
        matched_acte=matched,
        similarity_score=similarity,
        fraud_score=fraud_score,
        risk_level="HIGH" if fraud_score > 70 else "LOW",
        decision=decision,
        model_used="openai/gpt-4o-mini"
    )

    return {
        "analyse_id": str(analyse.id),
        "decision": decision,
        "fraud_score": fraud_score,
        "similarity_score": similarity,
        "matched": bool(matched),
        "extracted_data": extracted
    }