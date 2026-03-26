"""
URL configuration for fights app.
"""
from django.urls import path
from . import views

app_name = 'fights'

urlpatterns = [
    path('', views.FightListView.as_view(), name='list'),
    path('upcoming/', views.UpcomingFightsView.as_view(), name='upcoming'),
    path('schedule/', views.FightCreateView.as_view(), name='schedule'),
    path('<int:pk>/', views.FightDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.FightUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.FightDeleteView.as_view(), name='delete'),
    path('<int:pk>/result/', views.fight_record_result, name='record_result'),
    path('<int:pk>/cancel/', views.fight_cancel, name='cancel'),
]
