from rest_framework import serializers
from signalements.models import AnalyseIA


class AnalyseIASerializer(serializers.ModelSerializer):
    matched_data = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseIA
        fields = "__all__"

    # def get_matched_data(self, obj):
    #     if obj.matched_registre:
    #         entry = obj.matched_registre
    #         return {
    #             "nom": entry.nom,
    #             "prenom": entry.prenom,
    #             "date_naissance": entry.date_naissance.strftime("%d/%m/%Y") if entry.date_naissance else None,
    #             "numero_identification": entry.numero_identification,
    #             "type_acte": entry.type_acte,
    #             "centre": entry.centre.nom if entry.centre else None,
    #         }
    #     return None

    def get_statut(self, obj):
        mapping = {
            "FRAUD": "fraude",
            "SUSPECT": "suspect",
            "OK": "synchronise",
            "SAFE": "synchronise",
        }
        return mapping.get(obj.decision, "synchronise")

    def get_matched_data(self, obj):
        try:
            entry = obj.matched_registre

            if not entry:
                return None

            try:
                date_naissance = (
                    entry.date_naissance.strftime("%d/%m/%Y")
                    if entry.date_naissance
                    else None
                )
            except Exception:
                date_naissance = None

            return {
                "nom": getattr(entry, "nom", None),
                "prenom": getattr(entry, "prenom", None),
                "date_naissance": date_naissance,
                "numero_identification": getattr(entry, "numero_identification", None),
                "type_acte": getattr(entry, "type_acte", None),
                "centre": getattr(getattr(entry, "centre", None), "nom", None),
            }

        except Exception:
            return None