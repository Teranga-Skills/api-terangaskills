from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.services.pipeline import run_pipeline


class ScanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        file = request.FILES.get("document") or request.FILES.get("file")

        if not file:
            return Response({"error": "document requis (clé 'document' ou 'file')"}, status=400)

        result = run_pipeline(file, request.user)

        return Response(result)