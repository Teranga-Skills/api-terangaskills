from django.urls import path, include

from rest_framework.routers import DefaultRouter


from .views.centre_views import CentreEtatCivilViewSet



router = DefaultRouter()
from .views.reference_views import RegionViewSet, CommuneViewSet


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