# catalog/admin.py
from django.contrib import admin
from .models import Product, Category, Subscriber, ProductMedia


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 3  # Espacios por defecto para subir varios archivos de una vez
    fields = ['file', 'is_video', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductMediaInline]
    list_display = ('name', 'price', 'stock', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email',) 
    search_fields = ('email',)