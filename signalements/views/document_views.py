from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from signalements.models.document import Document
from signalements.serializers.document_serializer import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):

    queryset = Document.objects.all()

    serializer_class = DocumentSerializer

    permission_classes = [IsAuthenticated]