from django.contrib import admin
from django.urls import include, path

from market_data.views import LandingPageView, dashboard_view

urlpatterns = [
    path('', LandingPageView, name='landing'),
    path('admin/', admin.site.urls),
    path('market_data/', include('market_data.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
]
