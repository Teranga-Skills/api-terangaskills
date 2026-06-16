from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from signalements.models.acte import ActeEtatCivil
from signalements.serializers.acte_serializer import ActeEtatCivilSerializer


class ActeEtatCivilViewSet(viewsets.ModelViewSet):

    serializer_class = ActeEtatCivilSerializer
    permission_classes = [IsAuthenticated]

    queryset = ActeEtatCivil.objects.all()

    def get_queryset(self):

        queryset = super().get_queryset()

        centre_id = self.request.query_params.get("centre")

        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)

        return queryset