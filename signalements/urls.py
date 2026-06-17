from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.centre_views import CentreEtatCivilViewSet
from .views.reference_views import RegionViewSet, CommuneViewSet
from .views.citoyen_views import CitoyenViewSet
from .views.acte_views import ActeEtatCivilViewSet
from .views.document_views import DocumentViewSet
from signalements.views.synchronisation_views import (
    EnvoyerSynchronisationAPIView,
    StatutSynchronisationAPIView
)
from signalements.views.scan import ScanAPIView
from signalements.views.dashboard_views import (
    DashboardStatsAPIView,
    DashboardActesParCentreAPIView,
    DashboardFraudesAPIView,
    DashboardEvolutionAPIView,
    DashboardTopCentresRisqueAPIView,
    DashboardActesSuspectsAPIView
)
from signalements.views.copilot_views import CopilotAPIView

router = DefaultRouter()

router.register("documents", DocumentViewSet, basename="documents")
router.register("actes", ActeEtatCivilViewSet, basename="actes")
router.register("citoyens", CitoyenViewSet, basename="citoyens")
router.register("regions", RegionViewSet, basename="regions")
router.register("communes", CommuneViewSet, basename="communes")
router.register("centres", CentreEtatCivilViewSet, basename="centres")


urlpatterns = [

    path("", include(router.urls)),
    path("copilot/", CopilotAPIView.as_view()),
    path("synchronisation/envoyer/", EnvoyerSynchronisationAPIView.as_view()),
    path("synchronisation/statut/", StatutSynchronisationAPIView.as_view()),

    # SCAN IA
    path("scan/", ScanAPIView.as_view()),

    # DASHBOARD
    path("dashboard/stats/", DashboardStatsAPIView.as_view()),
    path("dashboard/centres/", DashboardActesParCentreAPIView.as_view()),
    path("dashboard/fraudes/", DashboardFraudesAPIView.as_view()),
    path("dashboard/evolution/", DashboardEvolutionAPIView.as_view()),
    path("dashboard/top-centres-risque/", DashboardTopCentresRisqueAPIView.as_view()),
    path("dashboard/actes-suspects/", DashboardActesSuspectsAPIView.as_view()),
]