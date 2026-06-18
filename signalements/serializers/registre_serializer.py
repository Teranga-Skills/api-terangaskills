from rest_framework import serializers

from signalements.models.registre import RegistreEtatCivil
from signalements.services.identification_utils import (
    identification_starts_with_digit,
    sanitize_identification,
)


class RegistreEtatCivilSerializer(serializers.ModelSerializer):

    centre_nom = serializers.CharField(source="centre.nom", read_only=True)

    class Meta:
        model = RegistreEtatCivil
        fields = [
            "id",
            "numero_identification",
            "nom",
            "prenom",
            "date_naissance",
            "type_acte",
            "numero_acte_officiel",
            "centre",
            "centre_nom",
            "actif",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "centre_nom"]

    def validate_numero_identification(self, value):
        sanitized = sanitize_identification(value)
        if not sanitized:
            raise serializers.ValidationError("Numéro d'identification invalide.")
        if not identification_starts_with_digit(sanitized):
            raise serializers.ValidationError(
                "Le numéro d'identification doit commencer par un chiffre."
            )
        return sanitized

    def validate_nom(self, value):
        return value.strip().upper()

    def validate_prenom(self, value):
        return value.strip()
