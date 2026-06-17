from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.models import AnalyseIA
from signalements.serializers.analyse_serializer import AnalyseIASerializer


# 1. LISTE DES ANALYSES
class AnalyseListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        analyses = AnalyseIA.objects.all().order_by("-created_at")
        serializer = AnalyseIASerializer(analyses, many=True)

        return Response(serializer.data)


# 2. DETAIL ANALYSE
class AnalyseDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, id):

        try:
            analyse = AnalyseIA.objects.get(id=id)
        except AnalyseIA.DoesNotExist:
            return Response({"error": "Analyse introuvable"}, status=404)

        serializer = AnalyseIASerializer(analyse)
        return Response(serializer.data)


# 3. LISTE FRAUDES
class FraudeListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        fraudes = AnalyseIA.objects.filter(decision="FRAUD").order_by("-created_at")
        serializer = AnalyseIASerializer(fraudes, many=True)

        return Response(serializer.data)


# 4. COMPARAISON (acte suspect vs original)
class AnalyseComparisonAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, id):

        try:
            analyse = AnalyseIA.objects.get(id=id)
        except AnalyseIA.DoesNotExist:
            return Response({"error": "Analyse introuvable"}, status=404)

        if not analyse.matched_acte:
            return Response({
                "message": "Aucun acte correspondant trouvé"
            })

        return Response({
            "acte_suspect": {
                "id": analyse.acte.id,
                "numero_acte": analyse.acte.numero_acte,
                "citoyen": str(analyse.acte.citoyen),
            },
            "acte_original": {
                "id": analyse.matched_acte.id,
                "numero_acte": analyse.matched_acte.numero_acte,
                "citoyen": str(analyse.matched_acte.citoyen),
            },
            "similarity_score": analyse.similarity_score,
            "fraud_score": analyse.fraud_score,
            "decision": analyse.decision
        })