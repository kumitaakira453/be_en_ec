from django.contrib import admin

from .models import OrderHistroy, Product, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderHistroy)
class OrderHistroyAdmin(admin.ModelAdmin):
    pass
