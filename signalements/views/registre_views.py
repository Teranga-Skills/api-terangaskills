from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from signalements.models.registre import RegistreEtatCivil
from signalements.serializers.registre_serializer import RegistreEtatCivilSerializer
from signalements.services.identification_utils import identifications_match


class RegistreEtatCivilViewSet(viewsets.ModelViewSet):

    queryset = RegistreEtatCivil.objects.select_related("centre").filter(actif=True)
    serializer_class = RegistreEtatCivilSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = RegistreEtatCivil.objects.select_related("centre").all()

        if self.action in ("list", "retrieve"):
            actif = self.request.query_params.get("actif")
            if actif is None:
                queryset = queryset.filter(actif=True)
            elif actif.lower() in ("0", "false", "no"):
                queryset = queryset.filter(actif=False)

        nom = self.request.query_params.get("nom")
        prenom = self.request.query_params.get("prenom")
        date_naissance = self.request.query_params.get("date_naissance")
        numero = self.request.query_params.get("numero_identification")

        if nom:
            queryset = queryset.filter(nom__icontains=nom.upper())
        if prenom:
            queryset = queryset.filter(prenom__icontains=prenom)
        if date_naissance:
            queryset = queryset.filter(date_naissance=date_naissance)
        if numero:
            ids_correspondants = [
                str(entry.id)
                for entry in queryset
                if identifications_match(entry.numero_identification, numero)
            ]
            queryset = queryset.filter(id__in=ids_correspondants)

        return queryset
