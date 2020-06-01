from django.contrib import admin

from .models import Product, Subscription

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id','name','price','product_type']
    ordering = ['-id']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id','name','price']
    ordering = ['-id']

