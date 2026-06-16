from rest_framework import serializers
from signalements.models.citoyen import Citoyen


class CitoyenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Citoyen
        fields = "__all__"