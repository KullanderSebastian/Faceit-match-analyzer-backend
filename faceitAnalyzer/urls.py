from django.urls import path
from faceitAnalyzer.quickstart import views

urlpatterns = [
    path("get_stats_for_game/<str:username>", views.get_stats_for_game),
]
