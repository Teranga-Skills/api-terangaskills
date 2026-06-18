from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from signalements.views import web_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(('users.urls', 'users'), namespace="users")),
    path("api/", include("signalements.urls")),
    path("api/", include("users.urls")),

    # Web Dashboard routes
    path('dashboard/', web_views.dashboard_view, name='dashboard'),
    path('dashboard/login/', web_views.login_view, name='login'),
    path('dashboard/logout/', web_views.logout_view, name='logout'),
    path('dashboard/citoyens/', web_views.citoyens_view, name='db_citoyens'),
    path('dashboard/actes/', web_views.actes_view, name='db_actes'),
    path('dashboard/centres/', web_views.centres_view, name='db_centres'),
    path('dashboard/analyses/', web_views.analyses_view, name='db_analyses'),
    path('dashboard/scan-upload/', web_views.scan_upload, name='db_scan_upload'),
    path('dashboard/alertes/', web_views.alertes_view, name='db_alertes'),
    path('dashboard/utilisateurs/', web_views.utilisateurs_view, name='db_utilisateurs'),
    path('dashboard/audit-logs/', web_views.audit_logs_view, name='db_audit_logs'),
    path('dashboard/sync/', web_views.sync_view, name='db_sync'),
    path('dashboard/copilot/', web_views.copilot_view, name='db_copilot'),
    path('dashboard/copilot/chat/', web_views.copilot_chat, name='db_copilot_chat'),

    # Documentation Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
