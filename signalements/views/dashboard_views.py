from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.models import AnalyseIA


class DashboardIAStatsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        total = AnalyseIA.objects.count()
        fraudes = AnalyseIA.objects.filter(decision="FRAUD").count()
        suspects = AnalyseIA.objects.filter(decision="SUSPECT").count()
        valides = AnalyseIA.objects.filter(decision="VALID").count()

        return Response({
            "total_scans": total,
            "fraudes_detectees": fraudes,
            "actes_suspects": suspects,
            "actes_valides": valides
        })