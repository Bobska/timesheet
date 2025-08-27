from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('daily/', views.daily_entry, name='daily_entry'),
    path('weekly/', views.weekly_summary, name='weekly_summary'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    # path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'), # To be implemented
]
