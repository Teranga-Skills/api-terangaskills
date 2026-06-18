from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.services.pipeline import run_analysis
from signalements.services.identification_utils import sanitize_identification


class AnalyseRegistreAPIView(APIView):
    """
    Compare les données saisies/extraites avec le registre officiel en base.
    Déclenché après validation du formulaire (bouton Analyser).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        nom = str(data.get("nom") or "UNKNOWN").upper().strip()
        prenom = str(data.get("prenom") or "UNKNOWN").strip()
        date_naissance = str(data.get("date_naissance") or data.get("dateNaissance") or "UNKNOWN").strip()
        raw_numero = str(
            data.get("numero_identification")
            or data.get("numeroDocument")
            or data.get("numero")
            or "UNKNOWN"
        ).strip()

        if nom == "UNKNOWN" and prenom == "UNKNOWN":
            nom_complet = str(data.get("nom_complet") or data.get("nomComplet") or "").strip()
            if nom_complet:
                parts = nom_complet.split()
                if len(parts) >= 2:
                    prenom = " ".join(parts[:-1])
                    nom = parts[-1].upper()
                else:
                    nom = nom_complet.upper()

        extracted = {
            "nom": nom,
            "prenom": prenom,
            "date_naissance": date_naissance,
            "numero_identification": sanitize_identification(raw_numero) or "UNKNOWN",
        }

        if extracted["numero_identification"] == "UNKNOWN":
            return Response(
                {"error": "Le numéro d'identification est requis pour l'analyse."},
                status=400,
            )

        result = run_analysis(extracted, user=request.user)
        return Response(result)
