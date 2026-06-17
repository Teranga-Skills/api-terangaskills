from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.services.pipeline import run_pipeline


class ScanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        file = request.FILES.get("document")

        if not file:
            return Response({"error": "document requis"}, status=400)

        result = run_pipeline(file, request.user)

        return Response(result)