from django.urls import path
from . import views

app_name = 'inspection'

urlpatterns = [
    path('', views.checklist_list, name='checklist_list'),
    path('checklist/<int:checklist_id>/', views.checklist_detail, name='checklist_detail'),
    path('records/', views.record_list, name='record_list'),
    path('records/<int:record_id>/', views.record_detail, name='record_detail'),
]
