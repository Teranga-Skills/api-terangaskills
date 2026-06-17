from rest_framework import serializers
from signalements.models import AnalyseIA


class AnalyseIASerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalyseIA
        fields = "__all__"