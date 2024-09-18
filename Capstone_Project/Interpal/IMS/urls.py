from django.urls import path
from . import views

urlpatterns = [
   path('', views.index, name='index'),
   path('another/', views.admin_2, name='Admin'),
]