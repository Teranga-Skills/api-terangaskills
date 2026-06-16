from django.urls import path, include

from rest_framework.routers import DefaultRouter


from .views.centre_views import CentreEtatCivilViewSet



router = DefaultRouter()


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