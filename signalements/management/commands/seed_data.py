from __future__ import annotations

import datetime
from django.core.management.base import BaseCommand
from signalements.models.centre import Region, Commune, CentreEtatCivil
from signalements.models.citoyen import Citoyen
from signalements.models.acte import ActeEtatCivil


class Command(BaseCommand):
    help = "Seed the database with regions, communes, centres, citizens, and acts."

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # 1. Regions
        r_dakar, _ = Region.objects.get_or_create(nom="Dakar")
        r_thies, _ = Region.objects.get_or_create(nom="Thiès")
        r_zig, _ = Region.objects.get_or_create(nom="Ziguinchor")

        # 2. Communes
        c_plateau, _ = Commune.objects.get_or_create(nom="Dakar-Plateau", region=r_dakar)
        c_thies_o, _ = Commune.objects.get_or_create(nom="Thiès-Ouest", region=r_thies)
        c_zig_com, _ = Commune.objects.get_or_create(nom="Ziguinchor-Commune", region=r_zig)

        # 3. Centres
        ctr_dakar, _ = CentreEtatCivil.objects.get_or_create(
            code="DK01",
            defaults={"nom": "Centre Dakar-Plateau", "region": r_dakar, "commune": c_plateau, "adresse": "Mairie de Dakar-Plateau"}
        )
        ctr_thies, _ = CentreEtatCivil.objects.get_or_create(
            code="TH01",
            defaults={"nom": "Centre Thiès-Ouest", "region": r_thies, "commune": c_thies_o, "adresse": "Mairie de Thiès-Ouest"}
        )
        ctr_zig, _ = CentreEtatCivil.objects.get_or_create(
            code="ZG01",
            defaults={"nom": "Centre de Ziguinchor", "region": r_zig, "commune": c_zig_com, "adresse": "Mairie de Ziguinchor"}
        )

        # 4. Citizens
        # Match Ousmane Sonko (simulate OCR scans)
        cit1, _ = Citoyen.objects.get_or_create(
            numero_identification="SN-1974-008273",
            defaults={"nom": "SONKO", "prenom": "Ousmane", "date_naissance": datetime.date(1974, 7, 15)}
        )
        # Match Moussa Diop (asset mock values)
        cit2, _ = Citoyen.objects.get_or_create(
            numero_identification="SN-2024-001234",
            defaults={"nom": "DIOP", "prenom": "Moussa", "date_naissance": datetime.date(1985, 3, 12)}
        )
        # Match Fatou Ndiaye (asset mock values)
        cit3, _ = Citoyen.objects.get_or_create(
            numero_identification="SN-P-2023-005678",
            defaults={"nom": "NDIAYE", "prenom": "Fatou", "date_naissance": datetime.date(1992, 11, 7)}
        )

        # 5. Acts
        ActeEtatCivil.objects.get_or_create(
            numero_acte="ACTE-1974-ZG01-0001",
            defaults={"type_acte": "NAISSANCE", "statut": "VALIDE", "citoyen": cit1, "centre": ctr_zig}
        )
        ActeEtatCivil.objects.get_or_create(
            numero_acte="ACTE-1985-DK01-0234",
            defaults={"type_acte": "NAISSANCE", "statut": "VALIDE", "citoyen": cit2, "centre": ctr_dakar}
        )
        ActeEtatCivil.objects.get_or_create(
            numero_acte="ACTE-1992-TH01-0567",
            defaults={"type_acte": "NAISSANCE", "statut": "VALIDE", "citoyen": cit3, "centre": ctr_thies}
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
