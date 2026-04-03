from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_activation_url(request, user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    rel = reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
    return request.build_absolute_uri(rel)


def send_activation_email(request, user) -> None:
    link = build_activation_url(request, user)
    subject = 'Подтвердите регистрацию — Тренажёры крупье'
    context = {'user': user, 'activation_link': link}
    body_html = render_to_string('registration/email/activation_body.html', context, request=request)
    body_txt = render_to_string('registration/email/activation_body.txt', context, request=request)
    send_mail(
        subject,
        body_txt,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=body_html,
        fail_silently=False,
    )
