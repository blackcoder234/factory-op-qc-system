from django.urls import path
from . import views

app_name = 'material_intake'

urlpatterns = [
    path('', views.batch_list, name='batch_list'),
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batch/<int:batch_id>/sncr/', views.raise_sncr, name='raise_sncr'),
]
