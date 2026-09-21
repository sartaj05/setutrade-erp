from datetime import date
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from api.models import Customer, Order, Product, Profile

ACCOUNTS = [
    ('owner', 'Arjun', 'Khanna', 'owner@setustock.demo', 'OWNER'),
    ('manager', 'Meera', 'Sethi', 'manager@setustock.demo', 'MANAGER'),
    ('sales', 'Rohit', 'Bansal', 'sales@setustock.demo', 'SALES'),
    ('warehouse', 'Imran', 'Ali', 'warehouse@setustock.demo', 'WAREHOUSE'),
    ('accountant', 'Nisha', 'Gupta', 'accountant@setustock.demo', 'ACCOUNTANT'),
]

PRODUCTS = [
    ('PC-25-RD','Polycab 2.5mm Wire Red','Wires & Cables',7,'coil',1820,2040,12,'A-01'),
    ('HA-LED-12','Havells 12W LED Bulb','Lighting',86,'pcs',118,145,30,'B-07'),
    ('AN-MCB-32','Anchor 32A DP MCB','Switchgear',24,'pcs',412,495,20,'C-11'),
    ('GM-PLT-8','GM 8 Module Plate','Switches',12,'pcs',176,225,15,'D-04'),
    ('RR-4SQ-BK','RR Kabel 4 sq mm Black','Wires & Cables',18,'coil',2960,3290,10,'A-04'),
    ('LE-FAN-48','Legrand Exhaust Fan 48W','Fans',9,'pcs',1780,2140,8,'E-02'),
]

CUSTOMERS = [
    ('C-101','R.K. Trading Co.','Ghaziabad','9810012233',58240,150000,date(2026,9,28)),
    ('C-102','Metro Electricals','Noida','9871123456',38400,100000,date(2026,9,9)),
    ('C-103','Ahuja Enterprises','Delhi','9899011122',0,200000,None),
    ('C-104','NCR Buildmart','Gurugram','9958012211',76750,250000,date(2026,9,25)),
    ('C-105','Sethi Hardware House','Faridabad','9818817717',124600,180000,date(2026,9,18)),
]

class Command(BaseCommand):
    help = 'Create SetuStock demo users and operational data.'

    def handle(self, *args, **options):
        for username, first, last, email, role in ACCOUNTS:
            user, _ = User.objects.get_or_create(username=username, defaults={'first_name': first, 'last_name': last, 'email': email})
            user.first_name, user.last_name, user.email = first, last, email
            user.set_password('demo123')
            user.save()
            Profile.objects.update_or_create(user=user, defaults={'role': role, 'business_name': 'Khanna Electrical Distributors'})

        for sku, name, category, stock, unit, buy, sell, reorder, location in PRODUCTS:
            Product.objects.update_or_create(sku=sku, defaults={'name':name,'category':category,'stock':stock,'unit':unit,'purchase_price':buy,'sell_price':sell,'reorder_level':reorder,'location':location})

        customer_map = {}
        for code, name, city, phone, outstanding, limit, due in CUSTOMERS:
            customer, _ = Customer.objects.update_or_create(code=code, defaults={'name':name,'city':city,'phone':phone,'outstanding':outstanding,'credit_limit':limit,'due_date':due})
            customer_map[code] = customer

        order_rows = [
            ('SO-1097','C-101',58240,'Ready','Credit',date(2026,9,21)),
            ('SO-1096','C-102',38400,'Processing','Overdue',date(2026,9,21)),
            ('SO-1095','C-103',76120,'Packed','Paid',date(2026,9,20)),
            ('SO-1094','C-104',29480,'Dispatched','Credit',date(2026,9,20)),
        ]
        for no, code, total, status, payment, order_date in order_rows:
            Order.objects.update_or_create(order_no=no, defaults={'customer':customer_map[code],'total':total,'status':status,'payment_status':payment,'order_date':order_date})
        self.stdout.write(self.style.SUCCESS('SetuStock demo data created.'))
