from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import PortadaView, TiendaListView, CartAddView, CartRemoveView, ProcesarCompraView, RuletaView, TragaperrasView, RavynGridView, BlackjackView, RegistroView

app_name = 'casino'

urlpatterns = [
    path('', PortadaView.as_view(), name='portada'),
    path('tienda/', TiendaListView.as_view(), name='tienda'),
    path('carrito/añadir/<int:paquete_id>/', CartAddView.as_view(), name='cart_add'),
    path('carrito/eliminar/<int:paquete_id>/', CartRemoveView.as_view(), name='cart_remove'),
    path('carrito/comprar/', ProcesarCompraView.as_view(), name='procesar_compra'),
    path('ruleta/', RuletaView.as_view(), name='ruleta'),
    path('slots/', TragaperrasView.as_view(), name='slots'),
    path('ravyn/', RavynGridView.as_view(), name='ravyn'),
    path('blackjack/', BlackjackView.as_view(), name='blackjack'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
