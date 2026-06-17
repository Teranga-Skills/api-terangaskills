"""
Service centralisé d'envoi d'emails de bienvenue.
Utilisé par le signal post_save (bootstrap superuser) et par la vue UserListCreateView (agent).
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)

# Instance partagée du générateur de tokens (thread-safe, sans état).
_token_generator = PasswordResetTokenGenerator()


def generate_set_password_link(user) -> str:
    """
    Génère un lien de définition de mot de passe sécurisé et à usage unique.

    Le token est invalidé automatiquement :
    - après expiration (PASSWORD_RESET_TIMEOUT, défaut Django : 3 jours)
    - dès que l'utilisateur change son mot de passe (le hash change)

    Aucune entrée en base n'est nécessaire.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = _token_generator.make_token(user)
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    return f"{frontend_url}/set-password/{uid}/{token}/"


def _build_bodies(user, link: str, role_label: str) -> tuple[str, str]:
    """
    Construit le corps texte et HTML de l'email de bienvenue.
    """
    timeout_seconds = getattr(settings, "PASSWORD_RESET_TIMEOUT", 259200)
    timeout_days = max(1, timeout_seconds // 86400)
    full_name = user.get_full_name() or user.email

    text_body = f"""\
Bonjour {full_name},

Votre {role_label} a été créé avec succès sur le système de gestion de l'état civil.

Pour définir votre mot de passe et accéder à votre espace, cliquez sur le lien ci-dessous :

{link}

Ce lien est valable {timeout_days} jour(s). Passé ce délai, vous devrez contacter votre administrateur.

Si vous n'attendiez pas cet email, ignorez-le — votre compte restera inactif tant que
vous n'aurez pas cliqué sur le lien.

Cordialement,
L'équipe de gestion de l'état civil.
""".strip()

    html_body = f"""\
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Définissez votre mot de passe</title>
</head>
<body style="margin:0; padding:0; background-color:#f3f4f6; font-family: Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff; border-radius:8px;
                      box-shadow:0 1px 4px rgba(0,0,0,0.08); overflow:hidden;">

          <!-- En-tête -->
          <tr>
            <td style="background:#1d4ed8; padding:28px 40px;">
              <p style="margin:0; color:#ffffff; font-size:20px; font-weight:bold;">
                Système de gestion de l'état civil
              </p>
            </td>
          </tr>

          <!-- Corps -->
          <tr>
            <td style="padding:36px 40px 24px;">
              <h2 style="margin:0 0 16px; color:#111827; font-size:22px;">
                Bienvenue, {full_name}&nbsp;!
              </h2>
              <p style="margin:0 0 12px; color:#374151; line-height:1.6;">
                Votre <strong>{role_label}</strong> a été créé avec succès.
                Vous devez définir votre mot de passe avant de pouvoir vous connecter.
              </p>
              <p style="margin:0 0 28px; color:#374151; line-height:1.6;">
                Cliquez sur le bouton ci-dessous pour choisir votre mot de passe&nbsp;:
              </p>

              <!-- Bouton CTA -->
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding:0 0 28px;">
                    <a href="{link}"
                       style="background:#1d4ed8; color:#ffffff; padding:14px 36px;
                              border-radius:6px; text-decoration:none; font-size:15px;
                              font-weight:bold; display:inline-block;">
                      Définir mon mot de passe
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Avertissement expiration -->
              <p style="margin:0; padding:16px; background:#fef9c3; border-radius:6px;
                        color:#713f12; font-size:13px; line-height:1.5;">
                ⏳ Ce lien est valable <strong>{timeout_days} jour(s)</strong>.
                Passé ce délai, contactez votre administrateur.
              </p>
            </td>
          </tr>

          <!-- Pied de page -->
          <tr>
            <td style="padding:20px 40px 32px; border-top:1px solid #e5e7eb;">
              <p style="margin:0 0 8px; color:#6b7280; font-size:12px; line-height:1.5;">
                Si le bouton ne fonctionne pas, copiez-collez ce lien dans votre navigateur&nbsp;:
              </p>
              <p style="margin:0; word-break:break-all;">
                <a href="{link}" style="color:#1d4ed8; font-size:12px;">{link}</a>
              </p>
              <p style="margin:16px 0 0; color:#9ca3af; font-size:11px;">
                Si vous n'attendiez pas cet email, ignorez-le.
                Votre compte reste inactif tant que vous n'avez pas défini de mot de passe.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>""".strip()

    return text_body, html_body


def send_welcome_email(user, role_label: str = "compte") -> bool:
    """
    Envoie un email de bienvenue avec un lien de définition de mot de passe.

    Args:
        user: Instance de CustomUser destinataire.
        role_label: Libellé métier affiché dans l'email (ex: "compte agent").

    Returns:
        True si l'envoi a réussi, False sinon (l'erreur est loguée, jamais propagée).
    """
    link = generate_set_password_link(user)
    subject = "Votre compte a été créé — Définissez votre mot de passe"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    text_body, html_body = _build_bodies(user, link, role_label)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Email de bienvenue envoyé à %s (rôle: %s)", user.email, role_label)
        return True
    except Exception as exc:
        logger.error(
            "Échec de l'envoi de l'email de bienvenue à %s : %s",
            user.email,
            exc,
            exc_info=True,
        )
        return False