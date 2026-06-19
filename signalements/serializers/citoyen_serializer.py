from rest_framework import serializers
from signalements.models.citoyen import Citoyen
from signalements.services.identification_utils import (
    identification_starts_with_digit,
    sanitize_identification,
)


class CitoyenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Citoyen
        fields = "__all__"

    def validate_numero_identification(self, value):
        if value in (None, ""):
            return value
        sanitized = sanitize_identification(value)
        if not sanitized:
            raise serializers.ValidationError("Numéro d'identification invalide.")
        if not identification_starts_with_digit(sanitized):
            raise serializers.ValidationError(
                "Le numéro d'identification doit commencer par un chiffre."
            )
        return sanitized