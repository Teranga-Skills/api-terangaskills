from django.contrib import admin
from django.utils.safestring import mark_safe
from signalements.models.centre import Region, Commune, CentreEtatCivil
from signalements.models.citoyen import Citoyen
from signalements.models.acte import ActeEtatCivil
from signalements.models.document import Document
from signalements.models.alerte import Alerte
from signalements.models.analyse_ia import AnalyseIA
from signalements.models.sync_queue import FileSynchronisation


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "created_at")
    search_fields = ("nom",)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "region", "created_at")
    list_filter = ("region",)
    search_fields = ("nom",)


@admin.register(CentreEtatCivil)
class CentreEtatCivilAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "nom", "region", "commune", "telephone")
    list_filter = ("region", "commune")
    search_fields = ("nom", "code")


@admin.register(Citoyen)
class CitoyenAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_identification", "nom", "prenom", "date_naissance", "created_at")
    search_fields = ("nom", "prenom", "numero_identification")


@admin.register(ActeEtatCivil)
class ActeEtatCivilAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_acte", "type_acte", "statut", "citoyen", "centre", "agent", "date_creation")
    list_filter = ("type_acte", "statut", "centre")
    search_fields = ("numero_acte", "citoyen__nom", "citoyen__prenom")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "acte", "qualite_scan", "hash_document", "created_at")
    search_fields = ("hash_document", "acte__numero_acte")


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ("id", "acte", "type_alerte", "niveau_severite", "est_resolue", "created_at")
    list_filter = ("type_alerte", "est_resolue", "niveau_severite")
    search_fields = ("acte__numero_acte", "message")


@admin.register(FileSynchronisation)
class FileSynchronisationAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "statut", "cree_le", "synchronise_le")
    list_filter = ("statut",)
    search_fields = ("utilisateur__email",)


@admin.register(AnalyseIA)
class AnalyseIAAdmin(admin.ModelAdmin):
    list_display = ("id", "decision", "fraud_score", "risk_level", "model_used", "created_at")
    list_filter = ("decision", "risk_level", "model_used")
    search_fields = ("ocr_text", "extracted_data")
    readonly_fields = ("details_comparaison", "ocr_text", "extracted_data", "acte", "matched_acte", "similarity_score", "fraud_score", "risk_level", "decision", "model_used", "created_at")
    exclude = ()

    @admin.display(description="Comparaison des données (Scannée vs Base SQL)")
    def details_comparaison(self, obj):
        extracted = obj.extracted_data or {}
        matched = obj.matched_acte
        
        scan_id = extracted.get("numero_identification") or "N/A"
        scan_nom = extracted.get("nom") or "N/A"
        scan_prenom = extracted.get("prenom") or "N/A"
        scan_dob = extracted.get("date_naissance") or "N/A"
        
        if matched and matched.citoyen:
            citoyen = matched.citoyen
            base_id = citoyen.numero_identification or "N/A"
            base_nom = citoyen.nom or "N/A"
            base_prenom = citoyen.prenom or "N/A"
            base_dob = citoyen.date_naissance.strftime("%d/%m/%Y") if citoyen.date_naissance else "N/A"
        else:
            base_id = "Non trouvé"
            base_nom = "Non trouvé"
            base_prenom = "Non trouvé"
            base_dob = "Non trouvé"
            
        def cell_style(diff):
            return "color: #dc2626; font-weight: bold; background-color: #fee2e2;" if diff else "color: #0f172a;"

        diff_id = str(scan_id).strip().lower() != str(base_id).strip().lower()
        diff_nom = str(scan_nom).strip().lower() != str(base_nom).strip().lower()
        diff_prenom = str(scan_prenom).strip().lower() != str(base_prenom).strip().lower()
        diff_dob = str(scan_dob).strip().lower() != str(base_dob).strip().lower()

        html = f"""
        <div style="max-width: 800px; margin-top: 10px; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px;">
                <thead>
                    <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #e2e8f0; font-weight: 600; color: #334155;">Champ</th>
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #e2e8f0; font-weight: 600; color: #334155;">Données OCR Scannées</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #334155;">Données de la Base (Originales)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 12px; font-weight: bold; border-right: 1px solid #e2e8f0; background-color: #f8fafc; color: #475569;">Numéro d'Identification</td>
                        <td style="padding: 12px; border-right: 1px solid #e2e8f0; {cell_style(diff_id)}">{scan_id}</td>
                        <td style="padding: 12px; color: #0f172a;">{base_id}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 12px; font-weight: bold; border-right: 1px solid #e2e8f0; background-color: #f8fafc; color: #475569;">Nom</td>
                        <td style="padding: 12px; border-right: 1px solid #e2e8f0; {cell_style(diff_nom)}">{scan_nom}</td>
                        <td style="padding: 12px; color: #0f172a;">{base_nom}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 12px; font-weight: bold; border-right: 1px solid #e2e8f0; background-color: #f8fafc; color: #475569;">Prénom</td>
                        <td style="padding: 12px; border-right: 1px solid #e2e8f0; {cell_style(diff_prenom)}">{scan_prenom}</td>
                        <td style="padding: 12px; color: #0f172a;">{base_prenom}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; border-right: 1px solid #e2e8f0; background-color: #f8fafc; color: #475569;">Date de Naissance</td>
                        <td style="padding: 12px; border-right: 1px solid #e2e8f0; {cell_style(diff_dob)}">{scan_dob}</td>
                        <td style="padding: 12px; color: #0f172a;">{base_dob}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        return mark_safe(html)
