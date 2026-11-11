from django.contrib import admin
from .models import Category, Product, ProductMedia, Subscriber

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Cambiamos 'category' por 'categories'
    list_display = ('name', 'price', 'stock', 'categories_list', 'is_active')
    list_filter = ('categories', 'is_active')  # Actualizado a 'categories'
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductMediaInline]

    def categories_list(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    categories_list.short_description = "Categorías"

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)