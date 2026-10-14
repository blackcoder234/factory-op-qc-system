from django.urls import path
from . import views

app_name = 'calibration'

urlpatterns = [
    path('', views.machine_lock_list, name='machine_lock_list'),
    path('lock/<int:machine_id>/', views.toggle_lock, name='toggle_lock'),
    path('maintenance/', views.maintenance_log, name='maintenance_log'),
]
