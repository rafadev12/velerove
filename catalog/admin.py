# catalog/admin.py
from django.contrib import admin
from .models import Product, Category, Subscriber

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    # Dejamos solo 'email' para evitar errores de campo no encontrado
    list_display = ('email',) 
    search_fields = ('email',)