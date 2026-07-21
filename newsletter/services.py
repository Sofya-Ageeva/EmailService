from django.core.mail import send_mail
from django.conf import settings
from .models import MailingAttempt

def send_mailing(mailing):
    """Отправка рассылки"""
    if not mailing.is_active():
        raise ValueError("Рассылка не активна (текущее время вне диапазона start_time - end_time)")

    recipients = mailing.recipients.all()
    attempts = []

    for client in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            status = MailingAttempt.AttemptStatus.SUCCESS
            response = "Письмо успешно отправлено"
        except Exception as e:
            status = MailingAttempt.AttemptStatus.FAILED
            response = str(e)

        attempts.append(
            MailingAttempt(
                mailing=mailing,
                client=client,
                status=status,
                server_response=response
            )
        )

    MailingAttempt.objects.bulk_create(attempts)
    return len(attempts)
