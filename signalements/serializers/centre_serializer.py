from rest_framework import serializers

from signalements.models.centre import CentreEtatCivil


class CentreEtatCivilSerializer(serializers.ModelSerializer):

    region_nom = serializers.CharField(
        source="region.nom",
        read_only=True
    )


    commune_nom = serializers.CharField(
        source="commune.nom",
        read_only=True
    )


    class Meta:

        model = CentreEtatCivil


        fields = [
            "id",
            "code",
            "nom",

            "region",
            "region_nom",

            "commune",
            "commune_nom",

            "adresse",
            "telephone"
        ]