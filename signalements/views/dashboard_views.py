from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Count, Q
from django.utils.timezone import now
from datetime import timedelta
import calendar

from signalements.models import ActeEtatCivil, AnalyseIA, CentreEtatCivil


# class DashboardIAStatsAPIView(APIView):

#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         total = AnalyseIA.objects.count()
#         fraudes = AnalyseIA.objects.filter(decision="FRAUD").count()
#         suspects = AnalyseIA.objects.filter(decision="SUSPECT").count()
#         valides = AnalyseIA.objects.filter(decision="VALID").count()

#         return Response({
#             "total_scans": total,
#             "fraudes_detectees": fraudes,
#             "actes_suspects": suspects,
#             "actes_valides": valides
#         })
        



# 1. STATISTIQUES GLOBALES
class DashboardStatsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "total_actes": ActeEtatCivil.objects.count(),
            "total_fraudes": AnalyseIA.objects.filter(decision="FRAUD").count(),
            "total_suspects": AnalyseIA.objects.filter(decision="SUSPECT").count(),
            "total_valides": AnalyseIA.objects.filter(decision="VALID").count(),
        })


# 2. ACTES PAR CENTRE
class DashboardActesParCentreAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = CentreEtatCivil.objects.annotate(
            total_actes=Count("actes")
        ).values("id", "nom", "total_actes")

        return Response(data)


# 3. FRAUDES
class DashboardFraudesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "fraudes_detectees": AnalyseIA.objects.filter(decision="FRAUD").count()
        })


# 4. EVOLUTION MENSUELLE
class DashboardEvolutionAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = now()
        data = []

        for i in range(6):

            date_ref = today - timedelta(days=30 * i)

            total = ActeEtatCivil.objects.filter(
                date_creation__year=date_ref.year,
                date_creation__month=date_ref.month
            ).count()

            data.append({
                "mois": calendar.month_name[date_ref.month],
                "total": total
            })

        return Response(data[::-1])


# 5. TOP CENTRES À RISQUE
class DashboardTopCentresRisqueAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        centres = CentreEtatCivil.objects.annotate(
            fraudes=Count(
                "actes__analyseia",
                filter=Q(actes__analyseia__decision="FRAUD")
            )
        ).order_by("-fraudes")[:5]

        return Response([
            {
                "centre": c.nom,
                "fraudes": c.fraudes
            }
            for c in centres
        ])


# 6. ACTES SUSPECTS
class DashboardActesSuspectsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        analyses = AnalyseIA.objects.filter(decision="SUSPECT").select_related("acte")[:50]

        return Response([
            {
                "acte_id": str(a.acte.id) if a.acte else None,
                "numero_acte": a.acte.numero_acte if a.acte else None,
                "fraud_score": a.fraud_score,
                "risk_level": a.risk_level,
                "centre": a.acte.centre.nom if a.acte and a.acte.centre else None
            }
            for a in analyses
        ])