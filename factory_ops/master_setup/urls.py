from django.urls import path
from . import views

app_name = 'master_setup'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('departments/', views.department_list, name='department_list'),
    path('machines/', views.machine_list, name='machine_list'),
    path('parts/', views.part_list, name='part_list'),
    path('gauges/', views.gauge_list, name='gauge_list'),
]
