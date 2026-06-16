from django.urls import path, include

from rest_framework.routers import DefaultRouter


from .views.centre_views import CentreEtatCivilViewSet



router = DefaultRouter()
from .views.reference_views import RegionViewSet, CommuneViewSet

from .views.citoyen_views import CitoyenViewSet
from .views.acte_views import ActeEtatCivilViewSet
from .views.document_views import DocumentViewSet

router.register("documents", DocumentViewSet, basename="documents")
router.register("actes", ActeEtatCivilViewSet, basename="actes")
router.register("citoyens", CitoyenViewSet, basename="citoyens")
router.register("regions", RegionViewSet, basename="regions")
router.register("communes", CommuneViewSet, basename="communes")

router.register(
    "centres",
    CentreEtatCivilViewSet,
    basename="centres"
)



urlpatterns = [

    path(
        "",
        include(router.urls)
    )

]