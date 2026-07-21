from django.views.generic import TemplateView
from django.db.models import Count, Q
from .models import Mailing, MailingStatus, Client


class HomeView(TemplateView):
    template_name = 'newsletter/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общее количество рассылок
        context['total_mailings'] = Mailing.objects.count()

        # Количество активных рассылок
        context['active_mailings'] = Mailing.objects.filter(
            status=MailingStatus.STARTED
        ).count()

        # Количество уникальных получателей
        context['total_clients'] = Client.objects.count()

        return context
