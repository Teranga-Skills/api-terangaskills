from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from signalements.models.centre import Region, Commune
from signalements.serializers.reference_serializer import (
    RegionSerializer,
    CommuneSerializer
)


# REGION CRUD
class RegionViewSet(viewsets.ModelViewSet):

    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated]


# COMMUNE CRUD
class CommuneViewSet(viewsets.ModelViewSet):

    queryset = Commune.objects.all()
    serializer_class = CommuneSerializer
    permission_classes = [IsAuthenticated]