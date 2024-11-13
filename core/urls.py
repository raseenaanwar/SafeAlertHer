# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('contacts/', views.manage_contacts, name='contacts'),
    path('contacts/edit/<int:contact_id>/', views.edit_contact, name='edit_contact'),
    path('contacts/delete/<int:contact_id>/', views.delete_contact, name='delete_contact'),
    path('alert/', views.create_alert, name='create_alert'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
]