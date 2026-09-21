from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
    path('auth/login/', views.login_view),
    path('auth/me/', views.me),
    path('dashboard/', views.dashboard),
    path('products/', views.products),
    path('customers/', views.customers),
    path('orders/', views.orders),
    path('invoices/', views.invoices),
    path('purchases/', views.purchases),
    path('suppliers/', views.suppliers),
    path('ledger/', views.ledger),
]
