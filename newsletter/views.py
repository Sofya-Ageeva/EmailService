from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from .models import Mailing, MailingStatus, Client, MailingAttempt
from mail_message.models import Message
from .forms import MailingForm
from .services import send_mailing

@method_decorator(cache_page(60 * 15), name='dispatch')
class HomeView(TemplateView):
    """Главная страница со статистикой"""
    template_name = 'newsletter/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_mailings'] = Mailing.objects.count()
        context['active_mailings'] = Mailing.objects.filter(
            status=MailingStatus.STARTED
        ).count()
        context['total_clients'] = Client.objects.count()
        context['latest_mailings'] = Mailing.objects.order_by('-created_at')[:5]

        if self.request.user.is_authenticated:
            from .models import MailingAttempt
            context['successful_attempts'] = MailingAttempt.objects.filter(
                mailing__owner=self.request.user,
                status=MailingAttempt.AttemptStatus.SUCCESS
            ).count()
            context['failed_attempts'] = MailingAttempt.objects.filter(
                mailing__owner=self.request.user,
                status=MailingAttempt.AttemptStatus.FAILED
            ).count()

        return context


@method_decorator(cache_page(60 * 5), name='dispatch')
class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок"""
    model = Mailing
    template_name = 'newsletter/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница рассылки"""
    model = Mailing
    template_name = 'newsletter/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'newsletter/mailing_form.html'
    success_url = reverse_lazy('newsletter:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Рассылка успешно создана.')
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'newsletter/mailing_form.html'
    success_url = reverse_lazy('newsletter:list')

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def test_func(self):
        mailing = self.get_object()
        user = self.request.user
        return user == mailing.owner or user.is_manager

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка успешно обновлена.')
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление рассылки"""
    model = Mailing
    template_name = 'newsletter/mailing_confirm_delete.html'
    success_url = reverse_lazy('newsletter:list')

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def test_func(self):
        mailing = self.get_object()
        user = self.request.user
        return user == mailing.owner or user.is_manager


class MailingSendView(LoginRequiredMixin, DetailView):
    """Отправка рассылки"""
    model = Mailing
    template_name = 'newsletter/mailing_send.html'
    context_object_name = 'mailing'

    def post(self, request, *args, **kwargs):
        mailing = self.get_object()
        
        try:
            count = send_mailing(mailing)
            messages.success(request, f'Рассылка успешно отправлена! Отправлено писем: {count}')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при отправке: {str(e)}')
        
        return redirect('newsletter:detail', pk=mailing.pk)


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Страница статистики пользователя"""
    template_name = 'newsletter/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Общая статистика
        context['total_mailings'] = Mailing.objects.filter(owner=user).count()
        context['total_clients'] = Client.objects.filter(owner=user).count()
        context['total_messages'] = Message.objects.filter(owner=user).count()

        # Статистика попыток
        attempts = MailingAttempt.objects.filter(mailing__owner=user)
        context['total_attempts'] = attempts.count()
        context['successful_attempts'] = attempts.filter(
            status=MailingAttempt.AttemptStatus.SUCCESS
        ).count()
        context['failed_attempts'] = attempts.filter(
            status=MailingAttempt.AttemptStatus.FAILED
        ).count()

        # Успешность в процентах
        if context['total_attempts'] > 0:
            context['success_rate'] = round(
                context['successful_attempts'] / context['total_attempts'] * 100, 1
            )
        else:
            context['success_rate'] = 0

        # Статистика по рассылкам
        context['mailing_stats'] = []
        for mailing in Mailing.objects.filter(owner=user):
            mailing_attempts = MailingAttempt.objects.filter(mailing=mailing)
            context['mailing_stats'].append({
                'mailing': mailing,
                'total': mailing_attempts.count(),
                'success': mailing_attempts.filter(
                    status=MailingAttempt.AttemptStatus.SUCCESS
                ).count(),
                'failed': mailing_attempts.filter(
                    status=MailingAttempt.AttemptStatus.FAILED
                ).count(),
            })

        return context
