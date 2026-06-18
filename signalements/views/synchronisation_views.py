from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from signalements.models.file_synchronisation import FileSynchronisation

class EnvoyerSynchronisationAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        donnees = request.data.get("donnees")

        if not donnees:
            return Response(
                {"erreur": "données manquantes"},
                status=400
            )

        file_sync = FileSynchronisation.objects.create(
            utilisateur=request.user,
            donnees=donnees,
            statut="EN_ATTENTE"
        )

        return Response({
            "message": "données reçues avec succès",
            "id_synchronisation": str(file_sync.id),
            "statut": "EN_ATTENTE"
        })
        
class StatutSynchronisationAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        files = FileSynchronisation.objects.filter(
            utilisateur=request.user
        ).order_by("-cree_le")

        return Response([
            {
                "id": str(f.id),
                "statut": f.statut,
                "cree_le": f.cree_le,
                "synchronise_le": f.synchronise_le
            }
            for f in files
        ])