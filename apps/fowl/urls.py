"""
URL configuration for fowl app.
"""
from django.urls import path
from . import views

app_name = 'fowl'

urlpatterns = [
    # Gamefowl URLs
    path('', views.FowlListView.as_view(), name='list'),
    path('add/', views.FowlCreateView.as_view(), name='create'),
    path('<int:pk>/', views.FowlDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.FowlUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.FowlDeleteView.as_view(), name='delete'),
    path('<int:pk>/bloodlines/', views.fowl_bloodlines_edit, name='bloodlines_edit'),
    path('<int:pk>/recalculate/', views.fowl_recalculate_bloodlines, name='recalculate'),

    # Bloodline URLs
    path('bloodlines/', views.BloodlineListView.as_view(), name='bloodline_list'),
    path('bloodlines/add/', views.BloodlineCreateView.as_view(), name='bloodline_create'),
    path('bloodlines/<int:pk>/', views.BloodlineDetailView.as_view(), name='bloodline_detail'),
    path('bloodlines/<int:pk>/edit/', views.BloodlineUpdateView.as_view(), name='bloodline_update'),
    path('bloodlines/<int:pk>/delete/', views.BloodlineDeleteView.as_view(), name='bloodline_delete'),
]
