from django.contrib import admin
from .models import Product, Order, Payment, Category, Review

# Register your models here.
admin.site.register (Product)
admin.site.register (Order)
admin.site.register (Payment)
admin.site.register (Category)
admin.site.register (Review)


admin.site.site_header = "Glai Export & Supply Admin"
admin.site.site_title = "Glai Admin Portal"
admin.site.index_title = "Welcome to Glai Export & Supply Dashboard"
