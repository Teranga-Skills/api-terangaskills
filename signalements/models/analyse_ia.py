from django.db import models
import uuid
from signalements.models import ActeEtatCivil

class AnalyseIA(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    acte = models.OneToOneField(ActeEtatCivil, on_delete=models.CASCADE)

    texte_ocr = models.TextField()

    donnees_extraites = models.JSONField()

    score_fraude = models.IntegerField(default=0)

    score_doublon = models.FloatField(default=0)

    niveau_risque = models.CharField(max_length=20)

    modele_utilise = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)