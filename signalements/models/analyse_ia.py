from django.db import models
import uuid
from signalements.models import ActeEtatCivil
from signalements.models.registre import RegistreEtatCivil


class AnalyseIA(models.Model):

    RISK_LEVEL = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    )

    DECISION = (
        ("VALID", "Valid"),
        ("SUSPECT", "Suspect"),
        ("FRAUD", "Fraud"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    acte = models.ForeignKey(ActeEtatCivil, on_delete=models.SET_NULL, null=True)

    ocr_text = models.TextField()

    extracted_data = models.JSONField()

    matched_acte = models.ForeignKey(
        ActeEtatCivil,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches"
    )

    matched_registre = models.ForeignKey(
        RegistreEtatCivil,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analyses",
    )

    similarity_score = models.FloatField(default=0)
    fraud_score = models.IntegerField(default=0)

    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL)
    decision = models.CharField(max_length=20, choices=DECISION)

    model_used = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)