from rest_framework import serializers

from signalements.models.acte import ActeEtatCivil
from signalements.services.acte_service import generer_numero_acte


class ActeEtatCivilSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActeEtatCivil
        fields = "__all__"
        read_only_fields = ["numero_acte", "statut", "agent"]


    def create(self, validated_data):

        request = self.context["request"]

        centre = validated_data["centre"]

        numero = generer_numero_acte(
            validated_data["type_acte"],
            centre.code
        )

        acte = ActeEtatCivil.objects.create(
            numero_acte=numero,
            agent=request.user,
            **validated_data
        )

        return acte