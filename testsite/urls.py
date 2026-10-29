from django.contrib import admin
from django.urls import path
from sourcing import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("client/", views.client_interface, name="client_interface"),
    path("supplier/", views.supplier_interface, name="supplier_interface"),
]
