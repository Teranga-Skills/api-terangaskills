from rest_framework import serializers
from signalements.models import AnalyseIA


class AnalyseIASerializer(serializers.ModelSerializer):
    matched_data = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseIA
        fields = "__all__"

    def get_matched_data(self, obj):
        if obj.matched_registre:
            entry = obj.matched_registre
            return {
                "nom": entry.nom,
                "prenom": entry.prenom,
                "date_naissance": entry.date_naissance.strftime("%d/%m/%Y") if entry.date_naissance else None,
                "numero_identification": entry.numero_identification,
                "type_acte": entry.type_acte,
                "centre": entry.centre.nom if entry.centre else None,
            }
        return None