import os
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from signalements.models import ActeEtatCivil, AnalyseIA, CentreEtatCivil


class CopilotAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        question = request.data.get("question")

        if not question:
            return Response({"error": "question requise"}, status=400)

        # 1. EXTRACTION DES DONNÉES UTILES (QUERY SIMPLE BACKEND)
        total_actes = ActeEtatCivil.objects.count()
        total_fraudes = AnalyseIA.objects.filter(decision="FRAUD").count()
        total_suspects = AnalyseIA.objects.filter(decision="SUSPECT").count()

        centres = CentreEtatCivil.objects.all()

        top_centres = CentreEtatCivil.objects.annotate(
            nb_fraudes=Count("actes__analyseia", filter=Q(actes__analyseia__decision="FRAUD"))
        ).order_by("-nb_fraudes")[:3]

        # 2. CONTEXTE À DONNER À L'IA
        context = {
            "total_actes": total_actes,
            "total_fraudes": total_fraudes,
            "total_suspects": total_suspects,
            "top_centres": [
                {"nom": c.nom, "fraudes": c.nb_fraudes}
                for c in top_centres
            ]
        }

        # 3. APPEL LLM (OPENROUTER)
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": """
Tu es un assistant administratif pour un système d'état civil.
Tu réponds uniquement à partir des données fournies.
Tu expliques clairement en français simple.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Question: {question}

Données système:
{context}

Réponds de manière claire et synthétique.
"""
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers)

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        return Response({
            "question": question,
            "answer": answer
        })