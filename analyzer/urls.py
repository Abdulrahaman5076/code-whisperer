"""
URL configuration for the analyzer app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('analyze/', views.analyze_view, name='analyze'),
    path('history/', views.history_view, name='history'),
    path('analysis/<str:code_hash>/', views.analysis_detail_view, name='analysis_detail'),
]