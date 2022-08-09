from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from django.conf import settings


def send_confirmation_code(user):
    confirmation_code = default_token_generator.make_token(user)
    subject = 'Код подтверждения YaMDb'
    message = f'{confirmation_code} - ваш код для авторизации на YaMDb'
    admin_email = settings.EMAIL_HOST_USER
    user_email = [user.email]
    return send_mail(subject, message, admin_email, user_email)
