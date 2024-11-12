# LB_API/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('address_to_boundaries/', views.address_to_boundaries_view, name='address_to_boundaries_view'),
]




