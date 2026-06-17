
from django.urls import path, include

from rest_framework.routers import DefaultRouter


from .views.centre_views import CentreEtatCivilViewSet

from .views.reference_views import RegionViewSet, CommuneViewSet
from .views.citoyen_views import CitoyenViewSet
from .views.acte_views import ActeEtatCivilViewSet
from .views.document_views import DocumentViewSet
from django.urls import path, include
from .views.centre_views import CentreEtatCivilViewSet

from rest_framework.routers import DefaultRouter





router = DefaultRouter()

from .views.scan import ScanAPIView



router = DefaultRouter()


router.register(
    "documents",
    DocumentViewSet,
    basename="documents"
)


router.register(
    "actes",
    ActeEtatCivilViewSet,
    basename="actes"
)


router.register(
    "citoyens",
    CitoyenViewSet,
    basename="citoyens"
)


router.register(
    "regions",
    RegionViewSet,
    basename="regions"
)


router.register(
    "communes",
    CommuneViewSet,
    basename="communes"
)


router.register(
    "centres",
    CentreEtatCivilViewSet,
    basename="centres"
)



urlpatterns = [

    path(
        "",
        include(router.urls)
    ),


    path(
        "scan/",
        ScanAPIView.as_view(),
        name="scan"
    ),

]