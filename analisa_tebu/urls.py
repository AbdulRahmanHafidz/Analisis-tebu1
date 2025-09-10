from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export_excel/', views.export_analisa_tebu_excel, name='export_analisa_tebu_excel'),
    path('tambah/', views.tambah_analisa, name='tambah_analisa'),
    path('edit/<int:pk>/', views.edit_analisa, name='edit_analisa'),
    path('hapus/<int:pk>/', views.hapus_analisa, name='hapus_analisa'),
    path('update_ph/<int:pk>/', views.update_ph, name='update_ph'),
]

