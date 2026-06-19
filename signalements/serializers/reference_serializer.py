from rest_framework import serializers
from signalements.models.centre import Region, Commune


class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region
        fields = ["id", "nom"]


class CommuneSerializer(serializers.ModelSerializer):

    region_nom = serializers.CharField(source="region.nom", read_only=True)

    class Meta:
        model = Commune
        fields = ["id", "nom", "region", "region_nom"]