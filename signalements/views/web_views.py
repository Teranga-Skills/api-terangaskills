import json
import os
import requests
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.contrib import messages
from django.utils.timezone import now
from datetime import timedelta
import calendar

from users.models import CustomUser, UserRole, AuditLog, AuditAction
from signalements.models import Citoyen, ActeEtatCivil, CentreEtatCivil, AnalyseIA, Alerte
from signalements.models.file_synchronisation import FileSynchronisation
from signalements.models.centre import Region, Commune
from signalements.services.pipeline import run_pipeline
from signalements.services.acte_service import generer_numero_acte


# ─── DECORATOR FOR ADMIN PROTECTION ───────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Seuls les administrateurs ont accès à cette console.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ─── UTILS ────────────────────────────────────────────────────────

def get_client_ip(request) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ─── AUTHENTICATION VIEWS ─────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == UserRole.ADMIN:
            return redirect('dashboard')
        else:
            messages.error(request, "Accès interdit aux non-administrateurs.")
            return redirect('login')
            
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, "Veuillez renseigner tous les champs.")
            return render(request, 'dashboard/login.html')
            
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.role == UserRole.ADMIN:
                auth_login(request, user)
                AuditLog.objects.create(
                    user=user,
                    action=AuditAction.LOGIN,
                    ip_address=get_client_ip(request),
                    success=True,
                    details={"interface": "web_dashboard"}
                )
                return redirect('dashboard')
            else:
                messages.error(request, "Seuls les administrateurs ont accès à cette interface.")
                AuditLog.objects.create(
                    user=user,
                    action=AuditAction.LOGIN_FAILED,
                    ip_address=get_client_ip(request),
                    success=False,
                    details={"interface": "web_dashboard", "error": "Rôle non autorisé"}
                )
        else:
            messages.error(request, "Adresse e-mail ou mot de passe incorrect.")
            # Chercher si l'utilisateur existe pour l'audit log
            u_exists = CustomUser.objects.filter(email__iexact=email).first()
            AuditLog.objects.create(
                user=u_exists,
                action=AuditAction.LOGIN_FAILED,
                ip_address=get_client_ip(request),
                success=False,
                details={"interface": "web_dashboard", "email": email, "error": "Identifiants invalides"}
            )
            
    return render(request, 'dashboard/login.html')


@login_required
def logout_view(request):
    AuditLog.objects.create(
        user=request.user,
        action=AuditAction.LOGOUT,
        ip_address=get_client_ip(request),
        success=True,
        details={"interface": "web_dashboard"}
    )
    auth_logout(request)
    return redirect('login')


# ─── CORE DASHBOARD ───────────────────────────────────────────────

@admin_required
def dashboard_view(request):
    total_actes = ActeEtatCivil.objects.count()
    total_fraudes = AnalyseIA.objects.filter(decision="FRAUD").count()
    total_suspects = AnalyseIA.objects.filter(decision="SUSPECT").count()
    total_valides = ActeEtatCivil.objects.filter(statut="VALIDE").count()
    
    avg_fraud_score = AnalyseIA.objects.aggregate(avg=Avg('fraud_score'))['avg'] or 0
    avg_fraud_score = round(avg_fraud_score, 1)
    
    compliance_rate = 100
    if total_actes > 0:
        compliance_rate = round((total_valides / total_actes) * 100, 1)
        
    recent_suspects = AnalyseIA.objects.filter(decision="SUSPECT").select_related('acte', 'acte__centre', 'acte__citoyen').order_by('-created_at')[:5]
    
    # Evolution mensuelle (6 derniers mois)
    today = now()
    months_labels = []
    months_counts = []
    for i in range(5, -1, -1):
        date_ref = today - timedelta(days=30 * i)
        cnt = ActeEtatCivil.objects.filter(
            date_creation__year=date_ref.year,
            date_creation__month=date_ref.month
        ).count()
        months_labels.append(calendar.month_name[date_ref.month].capitalize())
        months_counts.append(cnt)
        
    # Top centres actifs
    centres_data = CentreEtatCivil.objects.annotate(total=Count('actes')).order_by('-total')[:5]
    centres_labels = [c.nom for c in centres_data]
    centres_counts = [c.total for c in centres_data]
    
    # Decisions de l'IA
    decisions_counts = [
        AnalyseIA.objects.filter(decision="VALID").count(),
        AnalyseIA.objects.filter(decision="SUSPECT").count(),
        AnalyseIA.objects.filter(decision="FRAUD").count(),
    ]
    
    context = {
        "total_actes": total_actes,
        "total_fraudes": total_fraudes,
        "total_suspects": total_suspects,
        "total_valides": total_valides,
        "avg_fraud_score": avg_fraud_score,
        "compliance_rate": compliance_rate,
        "recent_suspects": recent_suspects,
        "months_labels": json.dumps(months_labels),
        "months_counts": json.dumps(months_counts),
        "centres_labels": json.dumps(centres_labels),
        "centres_counts": json.dumps(centres_counts),
        "decisions_counts": json.dumps(decisions_counts),
    }
    return render(request, 'dashboard/dashboard.html', context)


# ─── CITIZENS MANAGEMENT ──────────────────────────────────────────

@admin_required
def citoyens_view(request):
    query = Q()
    search_nom = request.GET.get('nom')
    search_prenom = request.GET.get('prenom')
    search_date = request.GET.get('date_naissance')
    search_ni = request.GET.get('numero_identification')
    
    if search_nom:
        query &= Q(nom__icontains=search_nom)
    if search_prenom:
        query &= Q(prenom__icontains=search_prenom)
    if search_date:
        query &= Q(date_naissance=search_date)
    if search_ni:
        query &= Q(numero_identification__icontains=search_ni)
        
    citoyens = Citoyen.objects.filter(query).order_by('-created_at')
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        date_naissance = request.POST.get('date_naissance')
        ni = request.POST.get('numero_identification')
        
        if not nom or not prenom:
            messages.error(request, "Le nom et le prénom sont requis.")
        else:
            if ni and Citoyen.objects.filter(numero_identification=ni).exists():
                messages.error(request, f"Un citoyen avec le numéro d'identification {ni} existe déjà.")
            else:
                citoyen = Citoyen.objects.create(
                    nom=nom,
                    prenom=prenom,
                    date_naissance=date_naissance or None,
                    numero_identification=ni or None
                )
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditAction.UPDATE_USER,
                    ip_address=get_client_ip(request),
                    success=True,
                    details={"action": "create_citoyen", "citoyen_id": str(citoyen.id)}
                )
                messages.success(request, f"Citoyen {prenom} {nom} enregistré avec succès.")
                return redirect('db_citoyens')
                
    context = {
        "citoyens": citoyens,
        "search_nom": search_nom or "",
        "search_prenom": search_prenom or "",
        "search_date": search_date or "",
        "search_ni": search_ni or "",
    }
    return render(request, 'dashboard/citoyens.html', context)


# ─── ACTES MANAGEMENT ─────────────────────────────────────────────

@admin_required
def actes_view(request):
    filter_centre = request.GET.get('centre')
    filter_type = request.GET.get('type_acte')
    filter_statut = request.GET.get('statut')
    
    query = Q()
    if filter_centre:
        query &= Q(centre_id=filter_centre)
    if filter_type:
        query &= Q(type_acte=filter_type)
    if filter_statut:
        query &= Q(statut=filter_statut)
        
    actes = ActeEtatCivil.objects.filter(query).select_related('citoyen', 'centre', 'agent').order_by('-date_creation')
    
    # AJAX Statut Update
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'update_status':
            acte_id = request.POST.get('acte_id')
            nouveau_statut = request.POST.get('statut')
            acte = get_object_or_404(ActeEtatCivil, id=acte_id)
            old_statut = acte.statut
            acte.statut = nouveau_statut
            acte.save()
            
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "update_acte_status", "acte_id": str(acte.id), "old_statut": old_statut, "new_statut": nouveau_statut}
            )
            return JsonResponse({"status": "success", "new_statut": acte.get_statut_display()})
            
    # Creation
    if request.method == 'POST' and not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        type_acte = request.POST.get('type_acte')
        citoyen_id = request.POST.get('citoyen')
        centre_id = request.POST.get('centre')
        
        citoyen = get_object_or_404(Citoyen, id=citoyen_id)
        centre = get_object_or_404(CentreEtatCivil, id=centre_id)
        
        numero = generer_numero_acte(type_acte, centre.code)
        
        acte = ActeEtatCivil.objects.create(
            type_acte=type_acte,
            citoyen=citoyen,
            centre=centre,
            numero_acte=numero,
            agent=request.user,
            statut="EN_ATTENTE"
        )
        
        AuditLog.objects.create(
            user=request.user,
            action=AuditAction.UPDATE_USER,
            ip_address=get_client_ip(request),
            success=True,
            details={"action": "create_acte", "acte_id": str(acte.id), "numero_acte": numero}
        )
        messages.success(request, f"Acte d'état civil {numero} enregistré avec succès.")
        return redirect('db_actes')
        
    centres = CentreEtatCivil.objects.all()
    citoyens = Citoyen.objects.all()
    
    context = {
        "actes": actes,
        "centres": centres,
        "citoyens": citoyens,
        "filter_centre": filter_centre or "",
        "filter_type": filter_type or "",
        "filter_statut": filter_statut or "",
    }
    return render(request, 'dashboard/actes.html', context)


# ─── CENTRES MANAGEMENT ───────────────────────────────────────────

@admin_required
def centres_view(request):
    filter_region = request.GET.get('region')
    filter_commune = request.GET.get('commune')
    
    query = Q()
    if filter_region:
        query &= Q(region_id=filter_region)
    if filter_commune:
        query &= Q(commune_id=filter_commune)
        
    centres = CentreEtatCivil.objects.filter(query).select_related('region', 'commune').annotate(
        agents_count=Count('agents', distinct=True),
        actes_count=Count('actes', distinct=True)
    ).order_by('nom')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        nom = request.POST.get('nom')
        region_id = request.POST.get('region')
        commune_id = request.POST.get('commune')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        
        region = get_object_or_404(Region, id=region_id)
        commune = get_object_or_404(Commune, id=commune_id)
        
        if CentreEtatCivil.objects.filter(code=code).exists():
            messages.error(request, f"Le code centre {code} est déjà utilisé.")
        else:
            centre = CentreEtatCivil.objects.create(
                code=code,
                nom=nom,
                region=region,
                commune=commune,
                adresse=adresse or None,
                telephone=telephone or None
            )
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "create_centre", "centre_id": str(centre.id), "code": code}
            )
            messages.success(request, f"Centre {nom} enregistré avec succès.")
            return redirect('db_centres')
            
    regions = Region.objects.all()
    communes = Commune.objects.all()
    
    context = {
        "centres": centres,
        "regions": regions,
        "communes": communes,
        "filter_region": filter_region or "",
        "filter_commune": filter_commune or "",
    }
    return render(request, 'dashboard/centres.html', context)


# ─── AI ANALYSES & SCANS ──────────────────────────────────────────

@admin_required
def analyses_view(request):
    analyses = AnalyseIA.objects.select_related('acte', 'matched_acte', 'acte__citoyen', 'matched_acte__citoyen').order_by('-created_at')
    
    total_scans = analyses.count()
    total_fraudes = analyses.filter(decision="FRAUD").count()
    total_suspects = analyses.filter(decision="SUSPECT").count()
    total_valides = analyses.filter(decision="VALID").count()
    
    context = {
        "analyses": analyses,
        "total_scans": total_scans,
        "total_fraudes": total_fraudes,
        "total_suspects": total_suspects,
        "total_valides": total_valides,
    }
    return render(request, 'dashboard/analyses.html', context)


@admin_required
def scan_upload(request):
    if request.method == 'POST' and request.FILES.get('document'):
        file = request.FILES['document']
        try:
            result = run_pipeline(file, request.user)
            # Create a user audit log for scanning
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "ai_document_scan", "decision": result.get("decision"), "fraud_score": result.get("fraud_score")}
            )
            return JsonResponse({"status": "success", "result": result})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Requête non autorisée."}, status=400)


# ─── SYSTEM ALERTS ────────────────────────────────────────────────

@admin_required
def alertes_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'resolve_alert':
            alerte_id = request.POST.get('alerte_id')
            alerte = get_object_or_404(Alerte, id=alerte_id)
            alerte.est_resolue = True
            alerte.save()
            
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "resolve_alerte", "alerte_id": str(alerte.id)}
            )
            return JsonResponse({"status": "success"})
            
    alertes = Alerte.objects.select_related('acte', 'acte__centre', 'acte__citoyen').order_by('-created_at')
    
    context = {
        "alertes": alertes,
    }
    return render(request, 'dashboard/alertes.html', context)


# ─── USER AGENTS MANAGEMENT ───────────────────────────────────────

@admin_required
def utilisateurs_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'toggle_status':
            target_id = request.POST.get('user_id')
            user_obj = get_object_or_404(CustomUser, id=target_id)
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "toggle_user_active", "target_user_id": user_obj.id, "is_active": user_obj.is_active}
            )
            return JsonResponse({"status": "success", "is_active": user_obj.is_active})
            
        elif action == 'assign_centre':
            target_id = request.POST.get('user_id')
            centre_id = request.POST.get('centre_id')
            user_obj = get_object_or_404(CustomUser, id=target_id)
            
            if centre_id:
                centre = get_object_or_404(CentreEtatCivil, id=centre_id)
                user_obj.centre = centre
            else:
                user_obj.centre = None
            user_obj.save()
            
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details={"action": "assign_user_centre", "target_user_id": user_obj.id, "centre_id": centre_id}
            )
            return JsonResponse({"status": "success"})
            
    if request.method == 'POST' and not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role = request.POST.get('role', UserRole.AGENT)
        centre_id = request.POST.get('centre')
        
        if not email or not password or not first_name or not last_name:
            messages.error(request, "Veuillez saisir tous les champs obligatoires.")
        else:
            if CustomUser.objects.filter(email__iexact=email).exists():
                messages.error(request, f"Un utilisateur avec l'adresse e-mail {email} existe déjà.")
            else:
                centre = None
                if role == UserRole.AGENT:
                    if not centre_id:
                        messages.error(request, "Un agent doit obligatoirement être affecté à un centre.")
                        return redirect('db_utilisateurs')
                    centre = get_object_or_404(CentreEtatCivil, id=centre_id)
                
                try:
                    user_obj = CustomUser.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        centre=centre
                    )
                    AuditLog.objects.create(
                        user=request.user,
                        action=AuditAction.CREATE_USER,
                        ip_address=get_client_ip(request),
                        success=True,
                        details={"target_user_id": user_obj.id, "email": email, "role": role}
                    )
                    messages.success(request, f"Compte de {first_name} {last_name} ({email}) créé avec succès.")
                    return redirect('db_utilisateurs')
                except Exception as e:
                    messages.error(request, f"Erreur de création : {e}")
                    
    users = CustomUser.objects.select_related('centre').order_by('-date_joined')
    centres = CentreEtatCivil.objects.all()
    
    context = {
        "users": users,
        "centres": centres,
        "roles": UserRole.choices,
    }
    return render(request, 'dashboard/utilisateurs.html', context)


# ─── AUDIT LOGS ───────────────────────────────────────────────────

@admin_required
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
        
    context = {
        "logs": logs[:100],  # Limite pour éviter de surcharger l'affichage
        "actions": AuditAction.choices,
        "action_filter": action_filter or "",
    }
    return render(request, 'dashboard/audit_logs.html', context)


# ─── OFFLINE SYNC QUEUE ────────────────────────────────────────────

@admin_required
def sync_view(request):
    queues = FileSynchronisation.objects.select_related('utilisateur').order_by('-cree_le')
    
    total_sync = queues.count()
    synced = queues.filter(statut="SYNCHRONISE").count()
    pending = queues.filter(statut="EN_ATTENTE").count()
    failed = queues.filter(statut="ECHEC").count()
    
    context = {
        "queues": queues,
        "total_sync": total_sync,
        "synced": synced,
        "pending": pending,
        "failed": failed,
    }
    return render(request, 'dashboard/sync.html', context)


# ─── AI COPILOT ───────────────────────────────────────────────────

def query_copilot(question, user):
    total_actes = ActeEtatCivil.objects.count()
    total_fraudes = AnalyseIA.objects.filter(decision="FRAUD").count()
    total_suspects = AnalyseIA.objects.filter(decision="SUSPECT").count()
    
    top_centres = CentreEtatCivil.objects.annotate(
        nb_fraudes=Count("actes__analyseia", filter=Q(actes__analyseia__decision="FRAUD"))
    ).order_by("-nb_fraudes")[:3]
    
    context_data = {
        "total_actes": total_actes,
        "total_fraudes": total_fraudes,
        "total_suspects": total_suspects,
        "top_centres": [
            {"nom": c.nom, "fraudes": c.nb_fraudes}
            for c in top_centres
        ]
    }
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        # Reponse simulation si pas de clé API
        return f"Bonjour ! **[Mode Demo DetectSen]** En analysant localement la base de données :\n\n" \
               f"- Nombre total d'actes : **{total_actes}**\n" \
               f"- Fraudes détectées : **{total_fraudes}**\n" \
               f"- Actes suspects en attente : **{total_suspects}**\n\n" \
               f"Les centres les plus touchés par les fraudes sont : " \
               f"{', '.join([f'*{c.nom}* ({c.nb_fraudes} cas)' for c in top_centres]) if top_centres else 'aucun pour le moment'}.\n\n" \
               f"Que souhaitez-vous vérifier ou modifier ?"
               
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Tu es l'assistant intelligent Copilot IA intégré au tableau de bord DetectSen de l'état civil sénégalais. Tu aides l'administrateur à comprendre l'activité, les fraudes et les statistiques. Utilise des puces et du gras pour formater des réponses claires en français."
            },
            {
                "role": "user",
                "content": f"Voici les données d'état civil consolidées en temps réel :\n{context_data}\n\nQuestion de l'administrateur : {question}"
            }
        ]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Le Copilot IA OpenRouter a renvoyé une erreur (Code {response.status_code}). Données locales : {context_data}"
    except Exception as e:
        return f"Erreur réseau avec le Copilot IA OpenRouter ({e}). Données locales : {context_data}"


@admin_required
def copilot_view(request):
    return render(request, 'dashboard/copilot.html')


@admin_required
def copilot_chat(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        question = request.POST.get('question')
        if not question:
            return JsonResponse({"status": "error", "message": "Veuillez entrer une question."}, status=400)
            
        answer = query_copilot(question, request.user)
        return JsonResponse({"status": "success", "answer": answer})
        
    return JsonResponse({"status": "error", "message": "Requête invalide."}, status=400)
