from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Tienda Pública
    path('', views.product_list, name='product_list'),
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Carrito
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<str:item_key>/', views.cart_remove, name='cart_remove'),
    path('cart/remove/<int:product_id>/<str:size>/', views.cart_remove, name='cart_remove_size'),
    path('checkout/', views.checkout, name='checkout'),

    # CRUD Privado
    path('gestion/producto/nuevo/', views.product_create, name='product_create'),
    path('gestion/producto/<int:pk>/editar/', views.product_update, name='product_update'),
    path('gestion/producto/<int:pk>/eliminar/', views.product_delete, name='product_delete'),

    # Varios
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('gift-cards/', views.gift_cards, name='gift_cards'),
]