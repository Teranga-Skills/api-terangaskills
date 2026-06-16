from rest_framework import serializers

from signalements.models.document import Document
from signalements.services.document_service import generer_hash_document


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["hash_document"]


    def create(self, validated_data):

        fichier = validated_data["fichier"]

        hash_doc = generer_hash_document(fichier)

        document = Document.objects.create(
            hash_document=hash_doc,
            **validated_data
        )

        return document