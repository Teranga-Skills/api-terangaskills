from rest_framework import serializers

from signalements.models.acte import ActeEtatCivil
from signalements.services.acte_service import generer_numero_acte


class ActeEtatCivilSerializer(serializers.ModelSerializer):
    derniere_analyse = serializers.SerializerMethodField()
    analyse_id = serializers.UUIDField(required=False, write_only=True)

    class Meta:
        model = ActeEtatCivil
        fields = [
            "id",
            "numero_acte",
            "type_acte",
            "statut",
            "citoyen",
            "centre",
            "agent",
            "date_creation",
            "derniere_analyse",
            "analyse_id",
        ]
        read_only_fields = ["numero_acte", "statut", "agent"]

    def get_derniere_analyse(self, obj):
        from signalements.models import AnalyseIA
        from signalements.serializers.analyse_serializer import AnalyseIASerializer
        analyse = AnalyseIA.objects.filter(acte=obj).order_by("-created_at").first()
        if analyse:
            return AnalyseIASerializer(analyse).data
        return None

    def create(self, validated_data):
        request = self.context["request"]
        analyse_id = validated_data.pop("analyse_id", None)

        centre = validated_data.get("centre")
        centre_code = centre.code if centre else "GEN"

        numero = generer_numero_acte(
            validated_data["type_acte"],
            centre_code
        )

        statut = "EN_ATTENTE"
        if analyse_id:
            try:
                from signalements.models import AnalyseIA
                analyse = AnalyseIA.objects.get(id=analyse_id)
                if analyse.decision in ["FRAUD", "SUSPECT"]:
                    statut = "SUSPECT"
                else:
                    statut = "VALIDE"
            except AnalyseIA.DoesNotExist:
                pass

        acte = ActeEtatCivil.objects.create(
            numero_acte=numero,
            agent=request.user,
            statut=statut,
            **validated_data
        )

        if analyse_id:
            try:
                from signalements.models import AnalyseIA
                analyse = AnalyseIA.objects.get(id=analyse_id)
                analyse.acte = acte
                analyse.save()
            except AnalyseIA.DoesNotExist:
                pass

        return acte