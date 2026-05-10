from decimal import Decimal
from django.conf import settings
from .models import PaqueteFichas

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, paquete):
        paquete_id = str(paquete.id)
        if paquete_id not in self.cart:
            self.cart[paquete_id] = {
                'precio': str(paquete.precio_dinero_ficticio),
                'cantidad': 1,
                'nombre': paquete.nombre
            }
        else:
            self.cart[paquete_id]['cantidad'] += 1
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, paquete):
        paquete_id = str(paquete.id)
        if paquete_id in self.cart:
            del self.cart[paquete_id]
            self.save()

    def clear(self):
        del self.session['cart']
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['precio']) * item['cantidad'] for item in self.cart.values())

    def __iter__(self):
        paquete_ids = self.cart.keys()
        paquetes = PaqueteFichas.objects.filter(id__in=paquete_ids)
        cart = self.cart.copy()
        for paquete in paquetes:
            cart[str(paquete.id)]['paquete'] = paquete

        for item in cart.values():
            item['precio'] = Decimal(item['precio'])
            item['total_price'] = item['precio'] * item['cantidad']
            yield item

    def __len__(self):
        return sum(item['cantidad'] for item in self.cart.values())
