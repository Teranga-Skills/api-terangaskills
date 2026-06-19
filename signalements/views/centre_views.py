from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


from signalements.models.centre import CentreEtatCivil

from signalements.serializers.centre_serializer import CentreEtatCivilSerializer



class CentreEtatCivilViewSet(viewsets.ModelViewSet):


    queryset = CentreEtatCivil.objects.all()


    serializer_class = CentreEtatCivilSerializer


    permission_classes = [
        IsAuthenticated
    ]