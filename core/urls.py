from django.urls import path

from . import views

urlpatterns = [
    path("", views.form_view, name="form"),
    path("orders/", views.orders_view, name="orders"),
    path("orders/<int:order_id>/", views.result_view, name="result"),
    path("orders/<int:order_id>/download/", views.download_view, name="download"),
    path("export/", views.export_csv, name="export"),
]
