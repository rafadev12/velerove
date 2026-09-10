import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import Product, Category, Subscriber, get_bcv_rate
from .forms import ProductForm

from django.core.cache import cache

def get_bcv_rate_cached():
    rate = cache.get('bcv_rate')
    if not rate:
        # Aquí va la función que consulta la tasa o scraping
        rate = fetch_bcv_rate_from_api() # O tu función get_bcv_rate()
        cache.set('bcv_rate', rate, 3600)  # Guarda la tasa en caché por 1 hora (3600 seg)
    return rate


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
                        fail_silently=False
                    )
                    messages.success(request, "¡Suscripción exitosa! Bienvenido al club VIP de VELERO.")
                except Exception:
                    messages.success(request, "Te has suscrito correctamente.")
            else:
                messages.info(request, "Este correo ya está registrado en nuestra lista.")
    
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


# ==========================================
# CATÁLOGO DE PRODUCTOS
# ==========================================

def product_list(request):
    selected_category = request.GET.get('category')
    categories = Category.objects.all()
    
    if selected_category and selected_category != 'all':
        products = Product.objects.filter(category__slug=selected_category).select_related('category')
    else:
        products = Product.objects.all().select_related('category')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Variantes de Color por nombre base
    base_name = product.name.split('-')[0].strip()
    color_variants = Product.objects.filter(
        name__icontains=base_name
    ).exclude(id=product.id)[:4]

    # Productos Relacionados
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:4]

    # Lógica de Tallas
    raw_sizes = list(product.sizes) if product.sizes else ['TU']
    is_single_size = 'TU' in raw_sizes or len(raw_sizes) == 0

    context = {
        'product': product,
        'color_variants': color_variants,
        'related_products': related_products,
        'sizes': raw_sizes,
        'is_single_size': is_single_size,
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
            'price': str(product.price),
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
    
    if not cart:
        subtotal_usd = 0.0
    else:
        subtotal_usd = sum(float(item['price']) * item['quantity'] for item in cart.values())

    bcv_rate = 814.69  # Tasa Oficial BCV
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
    bcv_rate = 814.69  # Tasa Oficial BCV
    total_ves = subtotal_usd * bcv_rate

    message_lines = [
        "🛒 *NUEVA ORDEN DE COMPRA - VELERO*",
        "------------------------------------",
        "*DETALLE DEL PEDIDO:*",
    ]

    for item_key, item in cart.items():
        # Fallback para obtener el nombre de la sesión o directo de BD si hiciera falta
        product_name = item.get('name') or item.get('product_name') or item.get('nombre')
        if not product_name and 'product_id' in item:
            try:
                prod = Product.objects.get(id=item['product_id'])
                product_name = prod.name
            except Product.DoesNotExist:
                product_name = "Producto"

        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        size_display = "Talla Única" if item.get('size') == 'TU' else item.get('size', 'N/A')
        
        line = f"• *{product_name}*\n  Talla: {size_display} | Cantidad: {quantity} | Precio: ${price} USD"
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

    whatsapp_phone = "584121143302"
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
            product = form.save(commit=False)
            selected_sizes = form.cleaned_data.get("sizes", [])
            product.sizes = ",".join(selected_sizes)
            product.save()
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