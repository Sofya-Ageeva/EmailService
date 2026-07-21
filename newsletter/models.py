from django.db import models
from django.utils import timezone
from django.conf import settings
from clients.models import Client
from mail_message.models import Message

class MailingStatus(models.TextChoices):
    CREATED = 'CREATED', 'Создана'
    STARTED = 'STARTED', 'Запущена'
    COMPLETED = 'COMPLETED', 'Завершена'

class Mailing(models.Model):
    start_time = models.DateTimeField(verbose_name='Дата и время начала')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания')
    status = models.CharField(
        max_length=20,
        choices=MailingStatus.choices,
        default=MailingStatus.CREATED,
        verbose_name='Статус'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Сообщение'
    )
    recipients = models.ManyToManyField(
        Client,
        related_name='mailings',
        verbose_name='Получатели'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Владелец'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']

    def __str__(self):
        return f"Рассылка #{self.id}: {self.message.subject}"

    def update_status(self):
        """Обновление статуса рассылки на основе текущего времени"""
        now = timezone.now()
        if now < self.start_time:
            new_status = MailingStatus.CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = MailingStatus.STARTED
        else:
            new_status = MailingStatus.COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])
        return self.status

    def is_active(self):
        """Проверка, активна ли рассылка"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class MailingAttempt(models.Model):
    class AttemptStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Успешно'
        FAILED = 'FAILED', 'Не успешно'

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Рассылка'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Получатель'
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время попытки'
    )
    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        verbose_name='Статус'
    )
    server_response = models.TextField(
        blank=True,
        verbose_name='Ответ сервера'
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Попытка #{self.id} для рассылки #{self.mailing.id}"
