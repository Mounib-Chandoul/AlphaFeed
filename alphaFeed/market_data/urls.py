from django.urls import path
from . import views

urlpatterns = [
    path('tickers/', views.TickerListView.as_view(), name='ticker-list'),
    path('analyze/', views.RunAnalysisView.as_view(), name='run-analysis'),
    path('trigger-bot/', views.trigger_bot, name='trigger-bot'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
