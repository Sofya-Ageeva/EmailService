from django.urls import path
from . import views

app_name = 'mail_message'

urlpatterns = [
    path('', views.MessageListView.as_view(), name='list'),
    path('create/', views.MessageCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.MessageUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MessageDeleteView.as_view(), name='delete'),
]
