from rest_framework import serializers
from signalements.models import AnalyseIA


class AnalyseIASerializer(serializers.ModelSerializer):
    matched_data = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseIA
        fields = "__all__"

    def get_matched_data(self, obj):
        if obj.matched_acte and obj.matched_acte.citoyen:
            citoyen = obj.matched_acte.citoyen
            return {
                "nom": citoyen.nom,
                "prenom": citoyen.prenom,
                "date_naissance": citoyen.date_naissance.strftime("%d/%m/%Y") if citoyen.date_naissance else None,
                "numero_identification": citoyen.numero_identification,
                "type_acte": obj.matched_acte.type_acte,
                "centre": obj.matched_acte.centre.nom if obj.matched_acte.centre else None,
            }
        return None