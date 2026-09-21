from django.contrib import admin
from .models import Customer, Invoice, Order, Product, Profile

admin.site.register(Profile)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Invoice)
