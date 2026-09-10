from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        """Inicializa el carrito de compras en la sesión."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, size='M', override_quantity=False):
        """Añade un producto al carrito o actualiza su cantidad."""
        product_id = str(product.id)
        item_key = f"{product_id}_{size}"

        if item_key not in self.cart:
            self.cart[item_key] = {
                'quantity': 0,
                'price': str(product.price),
                'size': size,
                'product_id': product_id
            }

        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity

        self.save()

    def remove(self, product, size='M'):
        """Elimina un producto del carrito por ID y Talla de forma segura."""
        product_id = str(product.id)
        item_key = f"{product_id}_{size}"

        if item_key in self.cart:
            del self.cart[item_key]
            self.save()
        elif product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """Itera sobre los elementos del carrito relacionándolos con la BD."""
        product_ids = []
        for item_key, item in self.cart.items():
            p_id = item.get('product_id') or item_key.split('_')[0]
            if str(p_id).isdigit():
                product_ids.append(int(p_id))

        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        for item_key, item in list(self.cart.items()):
            p_id = int(item.get('product_id') or item_key.split('_')[0])
            product = product_map.get(p_id)

            if product is None:
                continue

            item_data = item.copy()
            item_data['product'] = product
            item_data['price'] = Decimal(str(item_data['price']))
            item_data['total_price'] = item_data['price'] * item_data['quantity']
            item_data['item_key'] = item_key
            
            yield item_data

    def __len__(self):
        """Devuelve la cantidad total de artículos en el carrito."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calcula el monto total de la compra en USD."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """Vacía el carrito de la sesión."""
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        """Marca la sesión como modificada para asegurar que se guarde."""
        self.session.modified = True