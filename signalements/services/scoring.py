def compute_scores(extracted, matched):

    if not matched:
        return {
            "similarity": 0,
            "fraud_score": 30,
            "risk_level": "MEDIUM",
            "decision": "SUSPECT"
        }

    score = 0

    if extracted.get("nom") == matched.citoyen.nom:
        score += 40

    if extracted.get("prenom") == matched.citoyen.prenom:
        score += 30

    if str(extracted.get("date_naissance")) == str(matched.citoyen.date_naissance):
        score += 30

    similarity = score
    fraud_score = 100 - similarity

    if fraud_score >= 70:
        return {
            "similarity": similarity,
            "fraud_score": fraud_score,
            "risk_level": "HIGH",
            "decision": "FRAUD"
        }

    if fraud_score >= 40:
        return {
            "similarity": similarity,
            "fraud_score": fraud_score,
            "risk_level": "MEDIUM",
            "decision": "SUSPECT"
        }

    return {
        "similarity": similarity,
        "fraud_score": fraud_score,
        "risk_level": "LOW",
        "decision": "VALID"
    }