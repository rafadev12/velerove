import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from .models import Product, Category, Subscriber, get_bcv_rate
from .forms import ProductForm


# ==========================================
# BOLETÍN DE NOTICIAS / NEWSLETTER
# ==========================================

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if created:
                subject = f"🔥 Nuevo suscriptor VIP en VELERO: {email}"
                message = f"Un nuevo usuario se ha suscrito al boletín de VELERO.\n\nCorreo registrado: {email}"
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tu-correo@gmail.com')
                recipient_list = [from_email] 
                
                try:
                    send_mail(
                        subject, 
                        message, 
                        from_email, 
                        recipient_list, 
                        fail_silently=True
                    )
                    messages.success(request, "¡Suscripción exitosa! Bienvenido al club VIP de VELERO.")
                except Exception:
                    messages.success(request, "Te has suscrito correctamente.")
            else:
                messages.info(request, "Este correo ya está registrado en nuestra lista.")
    
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


# ==========================================
# CATÁLOGO DE PRODUCTOS (UNIFICADO Y BLINDADO)
# ==========================================

def product_list(request):
    selected_category = request.GET.get('category')
    categories = Category.objects.all()
    
    try:
        if selected_category and selected_category != 'all':
            # Filtrado adaptado al ManyToManyField (categories)
            products = Product.objects.filter(categories__slug=selected_category).prefetch_related('categories').distinct()
        else:
            products = Product.objects.all().prefetch_related('categories')
        
        # Blindaje de seguridad: si la consulta por categoría llega vacía, trae todo para que no quede en blanco
        if not products.exists() and selected_category and selected_category != 'all':
            products = Product.objects.all().prefetch_related('categories')
            
    except Exception as e:
        products = Product.objects.none()
        print(f"Error cargando productos en vistas: {e}")

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Obtenemos las categorías del producto actual
    product_categories = product.categories.all()

    # Filtramos para aislar la categoría principal de diseño y evitar que etiquetas
    # de marketing (como promociones o recién agregados) mezclen prendas de tipos distintos.
    main_categories = product_categories.exclude(slug__in=['promociones', 'recien-agregados', 'nuestras-promociones'])

    # Si la prenda solo tuviera etiquetas comerciales, usamos todas sus categorías como respaldo
    if not main_categories.exists():
        main_categories = product_categories

    # Variantes de color: Productos que compartan la categoría principal de diseño (excluyendo el actual)
    color_variants = Product.objects.filter(
        categories__in=main_categories
    ).exclude(id=product.id).distinct()[:5]

    # Productos Relacionados generales basados en la categoría principal de diseño
    related_products = Product.objects.filter(
        categories__in=main_categories
    ).exclude(id=product.id).distinct().order_by('?')[:4]

    context = {
        'product': product,
        'related_colors': color_variants,  
        'related_products': related_products,
        'sizes': product.sizes, # MultiSelectField maneja la lista directamente
        'is_single_size': 'TU' in product.sizes or len(product.sizes) == 0,
    }
    return render(request, 'catalog/product_detail.html', context)


# ==========================================
# CARRITO DE COMPRAS (SESIÓN)
# ==========================================

@require_POST
def cart_add(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get('size', 'TU')
    quantity = int(request.POST.get('quantity', 1))

    item_key = f"{product.id}_{size}"

    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        cart[item_key] = {
            'product_id': product.id,
            'name': product.name,
            'slug': product.slug, # <--- Agregado para links futuros si es necesario
            'price': str(product.price),
            'compare_price': str(product.compare_price) if product.compare_price else None, 
            'quantity': quantity,
            'size': size,
        }

    request.session['cart'] = cart
    return redirect('cart_detail')


def cart_remove(request, item_key):
    cart = request.session.get('cart', {})

    if item_key in cart:
        del cart[item_key]
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})
    
    subtotal_usd = sum(float(item['price']) * item['quantity'] for item in cart.values()) if cart else 0.0

    bcv_rate = get_bcv_rate()  # Tasa Oficial BCV actual
    total_ves = subtotal_usd * bcv_rate

    context = {
        'cart': cart,
        'subtotal_usd': subtotal_usd,
        'bcv_rate': bcv_rate,
        'total_ves': total_ves,
    }
    return render(request, 'catalog/cart_detail.html', context)


def checkout(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        return redirect('product_list')
        
    subtotal_usd = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in cart.values())
    bcv_rate = get_bcv_rate()  # Tasa Oficial BCV actual
    total_ves = subtotal_usd * bcv_rate

    # Obtenemos el dominio principal para construir la URL completa (ej: https://velerove.com)
    base_url = request.build_absolute_uri('/')[:-1]

    message_lines = [
        "🛒 *NUEVA ORDEN DE COMPRA - VELERO*",
        "------------------------------------",
        "*DETALLE DEL PEDIDO:*",
    ]

    # Extraemos los objetos reales de la base de datos
    product_ids = [item['product_id'] for item in cart.values() if 'product_id' in item]
    products_db = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    for item_key, item in cart.items():
        db_product = products_db.get(item.get('product_id'))
        
        product_name = item.get('name') or item.get('product_name') or "Producto"
        if not product_name and db_product:
            product_name = db_product.name

        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        size_display = "Talla Única" if item.get('size') == 'TU' else item.get('size', 'N/A')
        
        # Generamos el enlace oficial hacia la página del producto
        product_link = ""
        if db_product:
            # Creamos la ruta (ej: /producto/remera-oversize/) y la unimos al dominio
            path = reverse('product_detail', kwargs={'slug': db_product.slug})
            product_url = f"{base_url}{path}"
            product_link = f"\n  🔗 Ver en tienda: {product_url}"
        
        line = f"• *{product_name}*\n  Talla: {size_display} | Cantidad: {quantity} | Precio: ${price} USD{product_link}"
        message_lines.append(line)

    message_lines.extend([
        "------------------------------------",
        f"💵 *Subtotal USD:* ${subtotal_usd:.2f}",
        f"🇻🇪 *Tasa BCV:* {bcv_rate:.2f} Bs/USD",
        f"💳 *TOTAL VES:* {total_ves:,.2f} Bs",
        "------------------------------------",
        "Quedo a la espera de los datos de pago para realizar la transferencia / Pago Móvil."
    ])

    raw_message = "\n".join(message_lines)
    encoded_message = urllib.parse.quote(raw_message)

    whatsapp_phone = "584221143302"  # Número de WhatsApp de VELERO
    whatsapp_url = f"https://api.whatsapp.com/send?phone={whatsapp_phone}&text={encoded_message}"

    context = {
        'cart': cart,
        'subtotal_usd': subtotal_usd,
        'bcv_rate': bcv_rate,
        'total_ves': total_ves,
        'whatsapp_url': whatsapp_url,
    }
    return render(request, 'catalog/checkout.html', context)


# ==========================================
# SECCIONES ADICIONALES Y CRUD ADMIN
# ==========================================

def gift_cards(request):
    return render(request, 'catalog/gift_cards.html')


@staff_member_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() # El ModelForm guarda automáticamente las relaciones ManyToMany
            return redirect("product_list")
    else:
        form = ProductForm()

    return render(
        request,
        "catalog/product_form.html",
        {"form": form, "title": "Nuevo Producto"},
    )


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Editar Producto'})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'catalog/product_confirm_delete.html', {'product': product})