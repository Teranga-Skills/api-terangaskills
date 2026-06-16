from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from signalements.models.citoyen import Citoyen
from signalements.serializers.citoyen_serializer import CitoyenSerializer


class CitoyenViewSet(viewsets.ModelViewSet):

    queryset = Citoyen.objects.all()
    serializer_class = CitoyenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = super().get_queryset()

        nom = self.request.query_params.get("nom")
        prenom = self.request.query_params.get("prenom")
        date_naissance = self.request.query_params.get("date_naissance")
        numero = self.request.query_params.get("numero_identification")

        if nom:
            queryset = queryset.filter(nom__icontains=nom)

        if prenom:
            queryset = queryset.filter(prenom__icontains=prenom)

        if date_naissance:
            queryset = queryset.filter(date_naissance=date_naissance)

        if numero:
            queryset = queryset.filter(numero_identification=numero)

        return queryset