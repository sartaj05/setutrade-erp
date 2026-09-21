from django.contrib import admin
from .models import Customer, Order, Product, Profile

admin.site.register(Profile)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(Order)
