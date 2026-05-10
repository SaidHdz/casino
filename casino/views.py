import random
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse_lazy
from django.views.generic import ListView, View, TemplateView, CreateView

class RegistroView(CreateView):
    template_name = 'registration/registro.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cuenta creada con éxito. ¡Ahora puedes iniciar sesión!")
        return response

class CustomLoginView(DjangoLoginView):
    template_name = 'registration/login.html'

from django.http import JsonResponse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django import forms
from .models import PaqueteFichas, Perfil
from .cart import Cart
from datetime import timedelta

@method_decorator(login_required, name='dispatch')
class PortadaView(TemplateView):
    template_name = 'casino/portada.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            perfil = request.user.perfil
            ahora = timezone.now()
            
            # Recompensa Diaria: 500.00 cada 24 horas
            if ahora >= perfil.ultima_recarga + timedelta(days=1):
                perfil.dinero_ficticio += 500
                perfil.ultima_recarga = ahora
                perfil.save()
                messages.info(request, "¡Has recibido tu recompensa diaria de 500 monedas!")
        
        try:
            get_template(self.template_name)
            return super().get(request, *args, **kwargs)
        except TemplateDoesNotExist:
            return JsonResponse({
                'mensaje': 'Bienvenido al Casino',
                'recompensa_diaria': '500 monedas cada 24h',
                'estado': 'La plantilla portada.html no existe (Respaldo JSON)'
            })

class TiendaListView(ListView):
    model = PaqueteFichas
    template_name = 'casino/tienda.html'
    context_object_name = 'paquetes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context['cart'] = cart
        context['total_price'] = cart.get_total_price()
        return context

    def get(self, request, *args, **kwargs):
        try:
            get_template(self.template_name)
            return super().get(request, *args, **kwargs)
        except TemplateDoesNotExist:
            paquetes = self.get_queryset().values(
                'id', 'nombre', 'descripcion', 'cantidad_fichas', 'precio_dinero_ficticio'
            )
            return JsonResponse({'paquetes': list(paquetes)}, safe=False)

class CartAddView(View):
    def post(self, request, paquete_id):
        cart = Cart(request)
        paquete = get_object_or_404(PaqueteFichas, id=paquete_id)
        cart.add(paquete=paquete)
        return redirect('casino:tienda')

class CartRemoveView(View):
    def post(self, request, paquete_id):
        cart = Cart(request)
        paquete = get_object_or_404(PaqueteFichas, id=paquete_id)
        cart.remove(paquete)
        return redirect('casino:tienda')

from .forms import CompraFichasForm, ApuestaRuletaForm

@method_decorator(login_required, name='dispatch')
class ProcesarCompraView(View):
    def post(self, request):
        cart = Cart(request)
        perfil = request.user.perfil
        total_a_pagar = cart.get_total_price()

        form = CompraFichasForm(perfil=perfil, total_a_pagar=total_a_pagar)

        try:
            form.validar_compra()
            # Calcular total de fichas a sumar
            total_fichas = sum(item['paquete'].cantidad_fichas * item['cantidad'] for item in cart)
            
            # Actualizar perfil
            perfil.dinero_ficticio -= total_a_pagar
            perfil.fichas += total_fichas
            perfil.save()
            
            # Limpiar carrito
            cart.clear()
            messages.success(request, f"¡Compra realizada! Has obtenido {total_fichas} fichas.")
        except forms.ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
        
        return redirect('casino:tienda')

@method_decorator(login_required, name='dispatch')
class RuletaView(View):
    template_name = 'casino/ruleta.html'

    def get(self, request):
        form = ApuestaRuletaForm()
        try:
            get_template(self.template_name)
            return render(request, self.template_name, {'form': form})
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Roulette'})

    def post(self, request):
        perfil = request.user.perfil
        form = ApuestaRuletaForm(request.POST, perfil=perfil)
        contexto = {'form': form}
        
        if form.is_valid():
            tipo_apuesta = form.cleaned_data['tipo_apuesta']
            numero_elegido = form.cleaned_data.get('numero')
            color_elegido = form.cleaned_data.get('color')
            monto = form.cleaned_data['monto']

            # Cobrar apuesta
            perfil.fichas -= monto
            
            # Girar ruleta
            resultado_numero = random.randint(0, 36)
            if resultado_numero == 0:
                resultado_color = 'verde'
                angulo_final = 360 - 9 # Verde está en 0-18, centro 9
            elif resultado_numero % 2 == 0:
                resultado_color = 'rojo'
                i = random.randint(1, 9) # Rojo está en 36*i, excluyendo 0 (verde)
                angulo_final = 360 - (36 * i + 9)
            else:
                resultado_color = 'negro'
                i = random.randint(0, 9) # Negro está en 18 + 36*i
                angulo_final = 360 - (36 * i + 27)
                
            rotacion_total = 1800 + angulo_final # 5 vueltas (1800deg) + el ángulo de destino
                
            ganancia = 0
            win = False
            
            if tipo_apuesta == 'numero':
                if numero_elegido == resultado_numero:
                    win = True
                    ganancia = monto * 35
            elif tipo_apuesta == 'color':
                if color_elegido == resultado_color:
                    win = True
                    ganancia = monto * 2
                    
            if win:
                perfil.fichas += ganancia
                messages.success(request, f"¡Ganaste! Ha salido el {resultado_numero} {resultado_color}. Ganas {ganancia} fichas.")
            else:
                messages.error(request, f"Perdiste. Ha salido el {resultado_numero} {resultado_color}.")
                
            perfil.save()
            
            contexto['resultado_numero'] = resultado_numero
            contexto['resultado_color'] = resultado_color
            contexto['ganancia'] = ganancia
            contexto['rotacion_total'] = rotacion_total
            
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado': 'ok' if form.is_valid() else 'error',
                'errores': form.errors if not form.is_valid() else None,
                'resultado_numero': contexto.get('resultado_numero'),
                'resultado_color': contexto.get('resultado_color'),
                'ganancia': contexto.get('ganancia', 0),
                'rotacion_total': contexto.get('rotacion_total', 0),
                'fichas_actuales': perfil.fichas,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({
                'estado': 'ok' if form.is_valid() else 'error',
                'errores': form.errors if not form.is_valid() else None,
                'resultado_numero': contexto.get('resultado_numero'),
                'resultado_color': contexto.get('resultado_color'),
                'ganancia': contexto.get('ganancia', 0),
                'fichas_actuales': perfil.fichas
            })

@method_decorator(login_required, name='dispatch')
class TragaperrasView(View):
    template_name = 'casino/tragaperras.html'
    COSTO_GIRO = 10
    
    # Símbolos y sus multiplicadores (si salen 3 iguales)
    SIMBOLOS = ['🍒', '🍋', '🍉', '🔔', '💎', '⭐']
    PREMIOS = {
        '🍒': 20,   # x2
        '🍋': 30,   # x3
        '🍉': 50,   # x5
        '🔔': 100,  # x10
        '💎': 500,  # x50
        '⭐': 1000  # x100
    }

    def get(self, request):
        perfil = request.user.perfil
        contexto = {
            'fichas_actuales': perfil.fichas,
            'costo_giro': self.COSTO_GIRO,
            'premios': self.PREMIOS
        }
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Classic 3-Slot'})

    def post(self, request):
        perfil = request.user.perfil
        contexto = {
            'fichas_actuales': perfil.fichas,
            'costo_giro': self.COSTO_GIRO,
            'premios': self.PREMIOS
        }
        
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if perfil.fichas < self.COSTO_GIRO:
            messages.error(request, "No tienes fichas suficientes. ¡Ve a la tienda a recargar!")
            if is_ajax:
                mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                return JsonResponse({'estado': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
            try:
                get_template(self.template_name)
                return render(request, self.template_name, contexto)
            except TemplateDoesNotExist:
                return JsonResponse({'error': 'Saldo insuficiente'})

        # Cobrar apuesta
        perfil.fichas -= self.COSTO_GIRO
        
        # Generar resultado
        resultado = [random.choice(self.SIMBOLOS) for _ in range(3)]
        ganancia = 0
        win = False
        
        # Evaluar premio
        if resultado[0] == resultado[1] == resultado[2]:
            win = True
            simbolo_ganador = resultado[0]
            ganancia = self.PREMIOS[simbolo_ganador]
            perfil.fichas += ganancia
            messages.success(request, f"¡JACKPOT! 3x {simbolo_ganador}. Ganas {ganancia} fichas.")
        elif resultado[0] == resultado[1] or resultado[1] == resultado[2] or resultado[0] == resultado[2]:
            # Premio consuelo por 2 iguales (recuperas la apuesta)
            win = True
            ganancia = self.COSTO_GIRO
            perfil.fichas += ganancia
            messages.info(request, f"¡Casi! Tienes 2 símbolos iguales. Recuperas tus {ganancia} fichas.")
        else:
            messages.error(request, "Suerte para la próxima.")
            
        perfil.save()
        
        contexto.update({
            'fichas_actuales': perfil.fichas,
            'resultado': resultado,
            'ganancia': ganancia,
            'win': win
        })
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado': 'ok',
                'resultado': resultado,
                'ganancia': ganancia,
                'win': win,
                'fichas_actuales': perfil.fichas,
                'mensajes': mensajes_list
            })
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({
                'estado': 'ok',
                'resultado': resultado,
                'ganancia': ganancia,
                'fichas_actuales': perfil.fichas
            })

@method_decorator(login_required, name='dispatch')
class RavynGridView(View):
    template_name = 'casino/ravyn_grid.html'
    
    SIMBOLOS = ['🦍', '🦦', '🐒', '🧅']
    MULTIPLICADORES = {
        '🦍': 0.5,
        '🦦': 1.5,
        '🐒': 2.0,
        '🧅': 3.0
    }

    LINEAS = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Horizontales
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Verticales
        [0, 4, 8], [2, 4, 6]             # Diagonales
    ]

    def get(self, request):
        perfil = request.user.perfil
        contexto = {
            'fichas_actuales': perfil.fichas,
            'multiplicadores': self.MULTIPLICADORES
        }
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Ravyn Grid'})

    def post(self, request):
        perfil = request.user.perfil
        
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        try:
            monto_apuesta = int(request.POST.get('monto_apuesta', 0))
            if monto_apuesta <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Monto de apuesta inválido.")
            if is_ajax:
                mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                return JsonResponse({'estado': 'error', 'error': 'Monto inválido', 'mensajes': mensajes_list})
            return redirect('casino:ravyn')
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'multiplicadores': self.MULTIPLICADORES
        }
        
        if perfil.fichas < monto_apuesta:
            messages.error(request, "No tienes fichas suficientes. ¡Ve a la tienda a recargar!")
            if is_ajax:
                mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                return JsonResponse({'estado': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
            try:
                get_template(self.template_name)
                return render(request, self.template_name, contexto)
            except TemplateDoesNotExist:
                return JsonResponse({'error': 'Saldo insuficiente'})

        # Cobrar apuesta
        perfil.fichas -= monto_apuesta
        
        # Generar resultado (9 símbolos)
        resultado = [random.choice(self.SIMBOLOS) for _ in range(9)]
        
        multiplicador_total = 0.0
        lineas_ganadoras = []
        
        for idx, linea in enumerate(self.LINEAS):
            s1, s2, s3 = resultado[linea[0]], resultado[linea[1]], resultado[linea[2]]
            if s1 == s2 == s3:
                lineas_ganadoras.append(linea)
                multiplicador_total += self.MULTIPLICADORES[s1]
                
        ganancia = 0
        win = False
        
        if len(lineas_ganadoras) > 0:
            win = True
            ganancia = int(monto_apuesta * multiplicador_total)
            perfil.fichas += ganancia
            messages.success(request, f"¡Has ganado {ganancia} fichas! (Multiplicador Total: x{multiplicador_total:.1f})")
        else:
            messages.error(request, "Suerte para la próxima.")
            
        perfil.save()
        
        contexto.update({
            'fichas_actuales': perfil.fichas,
            'resultado': resultado,
            'lineas_ganadoras': lineas_ganadoras,
            'ganancia': ganancia,
            'win': win
        })
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado': 'ok',
                'resultado': resultado,
                'lineas_ganadoras': lineas_ganadoras,
                'ganancia': ganancia,
                'win': win,
                'fichas_actuales': perfil.fichas,
                'mensajes': mensajes_list
            })
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({
                'estado': 'ok',
                'resultado': resultado,
                'ganancia': ganancia,
                'fichas_actuales': perfil.fichas
            })

# --- BLACKJACK LOGIC ---
def crear_mazo():
    palos = ['♠', '♥', '♣', '♦']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    mazo = [{'valor': v, 'palo': p} for p in palos for v in valores]
    random.shuffle(mazo)
    return mazo

def calcular_puntaje(mano):
    suma = 0
    ases = 0
    for carta in mano:
        val = carta['valor']
        if val in ['J', 'Q', 'K']:
            suma += 10
        elif val == 'A':
            ases += 1
            suma += 11
        else:
            suma += int(val)
            
    while suma > 21 and ases:
        suma -= 10
        ases -= 1
    return suma

@method_decorator(login_required, name='dispatch')
class BlackjackView(View):
    template_name = 'casino/blackjack.html'

    def get(self, request):
        perfil = request.user.perfil
        
        # Inicializar sesión si no existe
        if 'bj_estado' not in request.session:
            request.session['bj_estado'] = 'esperando_apuesta'
            request.session['bj_apuesta'] = 0
            request.session['bj_mano_jugador'] = []
            request.session['bj_mano_dealer'] = []
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': request.session.get('bj_estado'),
            'apuesta_actual': request.session.get('bj_apuesta'),
            'mano_jugador': request.session.get('bj_mano_jugador'),
            'mano_dealer': request.session.get('bj_mano_dealer'),
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            'puntaje_dealer': calcular_puntaje(request.session.get('bj_mano_dealer', [])) if request.session.get('bj_estado') == 'terminado' else 0
        }
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Blackjack'})

    def post(self, request):
        perfil = request.user.perfil
        accion = request.POST.get('accion')
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        estado_actual = request.session.get('bj_estado', 'esperando_apuesta')
        
        ganancia = 0
        win = False
        empate = False

        if accion == 'apostar' and estado_actual in ['esperando_apuesta', 'terminado']:
            try:
                monto = int(request.POST.get('monto_apuesta', 0))
                if monto <= 0: raise ValueError
            except ValueError:
                messages.error(request, "Apuesta inválida.")
                return self._responder(request, is_ajax, perfil)
                
            if perfil.fichas < monto:
                messages.error(request, "No tienes fichas suficientes.")
                if is_ajax:
                    mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                    return JsonResponse({'estado_req': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
                return redirect('casino:blackjack')

            # Iniciar partida
            perfil.fichas -= monto
            perfil.save()
            
            mazo = crear_mazo()
            mano_jugador = [mazo.pop(), mazo.pop()]
            mano_dealer = [mazo.pop(), mazo.pop()]
            
            request.session['bj_mazo'] = mazo
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_apuesta'] = monto
            request.session['bj_estado'] = 'jugando'
            
            # Chequear Blackjack natural del jugador
            if calcular_puntaje(mano_jugador) == 21:
                request.session['bj_estado'] = 'terminado'
                win = True
                ganancia = int(monto * 2.5) # Blackjack paga 3 a 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡BLACKJACK NATURAL! Ganas {ganancia} fichas.")
                
        elif accion == 'pedir' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            
            mano_jugador.append(mazo.pop())
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mazo'] = mazo
            
            if calcular_puntaje(mano_jugador) > 21:
                request.session['bj_estado'] = 'terminado'
                messages.error(request, "¡Te has pasado de 21! Gana el Dealer.")

        elif accion == 'plantarse' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            mano_dealer = request.session.get('bj_mano_dealer', [])
            apuesta = request.session.get('bj_apuesta', 0)
            
            puntaje_jugador = calcular_puntaje(mano_jugador)
            puntaje_dealer = calcular_puntaje(mano_dealer)
            
            # Dealer pide hasta 17
            while puntaje_dealer < 17:
                mano_dealer.append(mazo.pop())
                puntaje_dealer = calcular_puntaje(mano_dealer)
                
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_mazo'] = mazo
            request.session['bj_estado'] = 'terminado'
            
            if puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
                win = True
                ganancia = apuesta * 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡Has ganado al Dealer! Te llevas {ganancia} fichas.")
            elif puntaje_jugador == puntaje_dealer:
                empate = True
                ganancia = apuesta # Devuelve la apuesta
                perfil.fichas += ganancia
                perfil.save()
                messages.info(request, "Empate. Recuperas tu apuesta.")
            else:
                messages.error(request, "Gana el Dealer.")

        else:
            messages.error(request, "Acción no válida en este momento.")

        # Guardar la sesión explícitamente porque modificamos listas mutables a veces
        request.session.modified = True
        return self._responder(request, is_ajax, perfil, ganancia=ganancia, win=win, empate=empate)

    def _responder(self, request, is_ajax, perfil, ganancia=0, win=False, empate=False):
        estado_bj = request.session.get('bj_estado')
        mano_dealer = request.session.get('bj_mano_dealer', [])
        
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': estado_bj,
            'apuesta_actual': request.session.get('bj_apuesta', 0),
            'mano_jugador': request.session.get('bj_mano_jugador', []),
            'mano_dealer': mano_dealer,
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            # Si se está jugando, oculta el puntaje total del dealer porque una carta está boca abajo
            'puntaje_dealer': calcular_puntaje(mano_dealer) if estado_bj == 'terminado' else 0,
            'ganancia': ganancia,
            'win': win,
            'empate': empate
        }
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado_req': 'ok',
                'contexto': contexto,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado_req': 'ok', 'contexto': contexto})

# --- BLACKJACK LOGIC ---
def crear_mazo():
    palos = ['♠', '♥', '♣', '♦']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    mazo = [{'valor': v, 'palo': p} for p in palos for v in valores]
    random.shuffle(mazo)
    return mazo

def calcular_puntaje(mano):
    suma = 0
    ases = 0
    for carta in mano:
        val = carta['valor']
        if val in ['J', 'Q', 'K']:
            suma += 10
        elif val == 'A':
            ases += 1
            suma += 11
        else:
            suma += int(val)
            
    while suma > 21 and ases:
        suma -= 10
        ases -= 1
    return suma

@method_decorator(login_required, name='dispatch')
class BlackjackView(View):
    template_name = 'casino/blackjack.html'

    def get(self, request):
        perfil = request.user.perfil
        
        # Inicializar sesión si no existe
        if 'bj_estado' not in request.session:
            request.session['bj_estado'] = 'esperando_apuesta'
            request.session['bj_apuesta'] = 0
            request.session['bj_mano_jugador'] = []
            request.session['bj_mano_dealer'] = []
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': request.session.get('bj_estado'),
            'apuesta_actual': request.session.get('bj_apuesta'),
            'mano_jugador': request.session.get('bj_mano_jugador'),
            'mano_dealer': request.session.get('bj_mano_dealer'),
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            'puntaje_dealer': calcular_puntaje(request.session.get('bj_mano_dealer', [])) if request.session.get('bj_estado') == 'terminado' else 0
        }
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Blackjack'})

    def post(self, request):
        perfil = request.user.perfil
        accion = request.POST.get('accion')
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        estado_actual = request.session.get('bj_estado', 'esperando_apuesta')
        
        ganancia = 0
        win = False
        empate = False

        if accion == 'apostar' and estado_actual in ['esperando_apuesta', 'terminado']:
            try:
                monto = int(request.POST.get('monto_apuesta', 0))
                if monto <= 0: raise ValueError
            except ValueError:
                messages.error(request, "Apuesta inválida.")
                return self._responder(request, is_ajax, perfil)
                
            if perfil.fichas < monto:
                messages.error(request, "No tienes fichas suficientes.")
                if is_ajax:
                    mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                    return JsonResponse({'estado_req': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
                return redirect('casino:blackjack')

            # Iniciar partida
            perfil.fichas -= monto
            perfil.save()
            
            mazo = crear_mazo()
            mano_jugador = [mazo.pop(), mazo.pop()]
            mano_dealer = [mazo.pop(), mazo.pop()]
            
            request.session['bj_mazo'] = mazo
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_apuesta'] = monto
            request.session['bj_estado'] = 'jugando'
            
            # Chequear Blackjack natural del jugador
            if calcular_puntaje(mano_jugador) == 21:
                request.session['bj_estado'] = 'terminado'
                win = True
                ganancia = int(monto * 2.5) # Blackjack paga 3 a 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡BLACKJACK NATURAL! Ganas {ganancia} fichas.")
                
        elif accion == 'pedir' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            
            mano_jugador.append(mazo.pop())
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mazo'] = mazo
            
            if calcular_puntaje(mano_jugador) > 21:
                request.session['bj_estado'] = 'terminado'
                messages.error(request, "¡Te has pasado de 21! Gana el Dealer.")

        elif accion == 'plantarse' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            mano_dealer = request.session.get('bj_mano_dealer', [])
            apuesta = request.session.get('bj_apuesta', 0)
            
            puntaje_jugador = calcular_puntaje(mano_jugador)
            puntaje_dealer = calcular_puntaje(mano_dealer)
            
            # Dealer pide hasta 17
            while puntaje_dealer < 17:
                mano_dealer.append(mazo.pop())
                puntaje_dealer = calcular_puntaje(mano_dealer)
                
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_mazo'] = mazo
            request.session['bj_estado'] = 'terminado'
            
            if puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
                win = True
                ganancia = apuesta * 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡Has ganado al Dealer! Te llevas {ganancia} fichas.")
            elif puntaje_jugador == puntaje_dealer:
                empate = True
                ganancia = apuesta # Devuelve la apuesta
                perfil.fichas += ganancia
                perfil.save()
                messages.info(request, "Empate. Recuperas tu apuesta.")
            else:
                messages.error(request, "Gana el Dealer.")

        else:
            messages.error(request, "Acción no válida en este momento.")

        # Guardar la sesión explícitamente porque modificamos listas mutables a veces
        request.session.modified = True
        return self._responder(request, is_ajax, perfil, ganancia=ganancia, win=win, empate=empate)

    def _responder(self, request, is_ajax, perfil, ganancia=0, win=False, empate=False):
        estado_bj = request.session.get('bj_estado')
        mano_dealer = request.session.get('bj_mano_dealer', [])
        
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': estado_bj,
            'apuesta_actual': request.session.get('bj_apuesta', 0),
            'mano_jugador': request.session.get('bj_mano_jugador', []),
            'mano_dealer': mano_dealer,
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            # Si se está jugando, oculta el puntaje total del dealer porque una carta está boca abajo
            'puntaje_dealer': calcular_puntaje(mano_dealer) if estado_bj == 'terminado' else 0,
            'ganancia': ganancia,
            'win': win,
            'empate': empate
        }
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado_req': 'ok',
                'contexto': contexto,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado_req': 'ok', 'contexto': contexto})

# --- BLACKJACK LOGIC ---
def crear_mazo():
    palos = ['♠', '♥', '♣', '♦']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    mazo = [{'valor': v, 'palo': p} for p in palos for v in valores]
    random.shuffle(mazo)
    return mazo

def calcular_puntaje(mano):
    suma = 0
    ases = 0
    for carta in mano:
        val = carta['valor']
        if val in ['J', 'Q', 'K']:
            suma += 10
        elif val == 'A':
            ases += 1
            suma += 11
        else:
            suma += int(val)
            
    while suma > 21 and ases:
        suma -= 10
        ases -= 1
    return suma

@method_decorator(login_required, name='dispatch')
class BlackjackView(View):
    template_name = 'casino/blackjack.html'

    def get(self, request):
        perfil = request.user.perfil
        
        # Inicializar sesión si no existe
        if 'bj_estado' not in request.session:
            request.session['bj_estado'] = 'esperando_apuesta'
            request.session['bj_apuesta'] = 0
            request.session['bj_mano_jugador'] = []
            request.session['bj_mano_dealer'] = []
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': request.session.get('bj_estado'),
            'apuesta_actual': request.session.get('bj_apuesta'),
            'mano_jugador': request.session.get('bj_mano_jugador'),
            'mano_dealer': request.session.get('bj_mano_dealer'),
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            'puntaje_dealer': calcular_puntaje(request.session.get('bj_mano_dealer', [])) if request.session.get('bj_estado') == 'terminado' else 0
        }
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Blackjack'})

    def post(self, request):
        perfil = request.user.perfil
        accion = request.POST.get('accion')
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        estado_actual = request.session.get('bj_estado', 'esperando_apuesta')
        
        ganancia = 0
        win = False
        empate = False

        if accion == 'apostar' and estado_actual in ['esperando_apuesta', 'terminado']:
            try:
                monto = int(request.POST.get('monto_apuesta', 0))
                if monto <= 0: raise ValueError
            except ValueError:
                messages.error(request, "Apuesta inválida.")
                return self._responder(request, is_ajax, perfil)
                
            if perfil.fichas < monto:
                messages.error(request, "No tienes fichas suficientes.")
                if is_ajax:
                    mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                    return JsonResponse({'estado_req': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
                return redirect('casino:blackjack')

            # Iniciar partida
            perfil.fichas -= monto
            perfil.save()
            
            mazo = crear_mazo()
            mano_jugador = [mazo.pop(), mazo.pop()]
            mano_dealer = [mazo.pop(), mazo.pop()]
            
            request.session['bj_mazo'] = mazo
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_apuesta'] = monto
            request.session['bj_estado'] = 'jugando'
            
            # Chequear Blackjack natural del jugador
            if calcular_puntaje(mano_jugador) == 21:
                request.session['bj_estado'] = 'terminado'
                win = True
                ganancia = int(monto * 2.5) # Blackjack paga 3 a 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡BLACKJACK NATURAL! Ganas {ganancia} fichas.")
                
        elif accion == 'pedir' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            
            mano_jugador.append(mazo.pop())
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mazo'] = mazo
            
            if calcular_puntaje(mano_jugador) > 21:
                request.session['bj_estado'] = 'terminado'
                messages.error(request, "¡Te has pasado de 21! Gana el Dealer.")

        elif accion == 'plantarse' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            mano_dealer = request.session.get('bj_mano_dealer', [])
            apuesta = request.session.get('bj_apuesta', 0)
            
            puntaje_jugador = calcular_puntaje(mano_jugador)
            puntaje_dealer = calcular_puntaje(mano_dealer)
            
            # Dealer pide hasta 17
            while puntaje_dealer < 17:
                mano_dealer.append(mazo.pop())
                puntaje_dealer = calcular_puntaje(mano_dealer)
                
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_mazo'] = mazo
            request.session['bj_estado'] = 'terminado'
            
            if puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
                win = True
                ganancia = apuesta * 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡Has ganado al Dealer! Te llevas {ganancia} fichas.")
            elif puntaje_jugador == puntaje_dealer:
                empate = True
                ganancia = apuesta # Devuelve la apuesta
                perfil.fichas += ganancia
                perfil.save()
                messages.info(request, "Empate. Recuperas tu apuesta.")
            else:
                messages.error(request, "Gana el Dealer.")

        else:
            messages.error(request, "Acción no válida en este momento.")

        # Guardar la sesión explícitamente porque modificamos listas mutables a veces
        request.session.modified = True
        return self._responder(request, is_ajax, perfil, ganancia=ganancia, win=win, empate=empate)

    def _responder(self, request, is_ajax, perfil, ganancia=0, win=False, empate=False):
        estado_bj = request.session.get('bj_estado')
        mano_dealer = request.session.get('bj_mano_dealer', [])
        
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': estado_bj,
            'apuesta_actual': request.session.get('bj_apuesta', 0),
            'mano_jugador': request.session.get('bj_mano_jugador', []),
            'mano_dealer': mano_dealer,
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            # Si se está jugando, oculta el puntaje total del dealer porque una carta está boca abajo
            'puntaje_dealer': calcular_puntaje(mano_dealer) if estado_bj == 'terminado' else 0,
            'ganancia': ganancia,
            'win': win,
            'empate': empate
        }
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado_req': 'ok',
                'contexto': contexto,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado_req': 'ok', 'contexto': contexto})

# --- BLACKJACK LOGIC ---
def crear_mazo():
    palos = ['♠', '♥', '♣', '♦']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    mazo = [{'valor': v, 'palo': p} for p in palos for v in valores]
    random.shuffle(mazo)
    return mazo

def calcular_puntaje(mano):
    suma = 0
    ases = 0
    for carta in mano:
        val = carta['valor']
        if val in ['J', 'Q', 'K']:
            suma += 10
        elif val == 'A':
            ases += 1
            suma += 11
        else:
            suma += int(val)
            
    while suma > 21 and ases:
        suma -= 10
        ases -= 1
    return suma

@method_decorator(login_required, name='dispatch')
class BlackjackView(View):
    template_name = 'casino/blackjack.html'

    def get(self, request):
        perfil = request.user.perfil
        
        # Inicializar sesión si no existe
        if 'bj_estado' not in request.session:
            request.session['bj_estado'] = 'esperando_apuesta'
            request.session['bj_apuesta'] = 0
            request.session['bj_mano_jugador'] = []
            request.session['bj_mano_dealer'] = []
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': request.session.get('bj_estado'),
            'apuesta_actual': request.session.get('bj_apuesta'),
            'mano_jugador': request.session.get('bj_mano_jugador'),
            'mano_dealer': request.session.get('bj_mano_dealer'),
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            'puntaje_dealer': calcular_puntaje(request.session.get('bj_mano_dealer', [])) if request.session.get('bj_estado') == 'terminado' else 0
        }
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Blackjack'})

    def post(self, request):
        perfil = request.user.perfil
        accion = request.POST.get('accion')
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        estado_actual = request.session.get('bj_estado', 'esperando_apuesta')
        
        ganancia = 0
        win = False
        empate = False

        if accion == 'apostar' and estado_actual in ['esperando_apuesta', 'terminado']:
            try:
                monto = int(request.POST.get('monto_apuesta', 0))
                if monto <= 0: raise ValueError
            except ValueError:
                messages.error(request, "Apuesta inválida.")
                return self._responder(request, is_ajax, perfil)
                
            if perfil.fichas < monto:
                messages.error(request, "No tienes fichas suficientes.")
                if is_ajax:
                    mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                    return JsonResponse({'estado_req': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
                return redirect('casino:blackjack')

            # Iniciar partida
            perfil.fichas -= monto
            perfil.save()
            
            mazo = crear_mazo()
            mano_jugador = [mazo.pop(), mazo.pop()]
            mano_dealer = [mazo.pop(), mazo.pop()]
            
            request.session['bj_mazo'] = mazo
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_apuesta'] = monto
            request.session['bj_estado'] = 'jugando'
            
            # Chequear Blackjack natural del jugador
            if calcular_puntaje(mano_jugador) == 21:
                request.session['bj_estado'] = 'terminado'
                win = True
                ganancia = int(monto * 2.5) # Blackjack paga 3 a 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡BLACKJACK NATURAL! Ganas {ganancia} fichas.")
                
        elif accion == 'pedir' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            
            mano_jugador.append(mazo.pop())
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mazo'] = mazo
            
            if calcular_puntaje(mano_jugador) > 21:
                request.session['bj_estado'] = 'terminado'
                messages.error(request, "¡Te has pasado de 21! Gana el Dealer.")

        elif accion == 'plantarse' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            mano_dealer = request.session.get('bj_mano_dealer', [])
            apuesta = request.session.get('bj_apuesta', 0)
            
            puntaje_jugador = calcular_puntaje(mano_jugador)
            puntaje_dealer = calcular_puntaje(mano_dealer)
            
            # Dealer pide hasta 17
            while puntaje_dealer < 17:
                mano_dealer.append(mazo.pop())
                puntaje_dealer = calcular_puntaje(mano_dealer)
                
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_mazo'] = mazo
            request.session['bj_estado'] = 'terminado'
            
            if puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
                win = True
                ganancia = apuesta * 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡Has ganado al Dealer! Te llevas {ganancia} fichas.")
            elif puntaje_jugador == puntaje_dealer:
                empate = True
                ganancia = apuesta # Devuelve la apuesta
                perfil.fichas += ganancia
                perfil.save()
                messages.info(request, "Empate. Recuperas tu apuesta.")
            else:
                messages.error(request, "Gana el Dealer.")

        else:
            messages.error(request, "Acción no válida en este momento.")

        # Guardar la sesión explícitamente porque modificamos listas mutables a veces
        request.session.modified = True
        return self._responder(request, is_ajax, perfil, ganancia=ganancia, win=win, empate=empate)

    def _responder(self, request, is_ajax, perfil, ganancia=0, win=False, empate=False):
        estado_bj = request.session.get('bj_estado')
        mano_dealer = request.session.get('bj_mano_dealer', [])
        
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': estado_bj,
            'apuesta_actual': request.session.get('bj_apuesta', 0),
            'mano_jugador': request.session.get('bj_mano_jugador', []),
            'mano_dealer': mano_dealer,
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            # Si se está jugando, oculta el puntaje total del dealer porque una carta está boca abajo
            'puntaje_dealer': calcular_puntaje(mano_dealer) if estado_bj == 'terminado' else 0,
            'ganancia': ganancia,
            'win': win,
            'empate': empate
        }
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado_req': 'ok',
                'contexto': contexto,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado_req': 'ok', 'contexto': contexto})

# --- BLACKJACK LOGIC ---
def crear_mazo():
    palos = ['♠', '♥', '♣', '♦']
    valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    mazo = [{'valor': v, 'palo': p} for p in palos for v in valores]
    random.shuffle(mazo)
    return mazo

def calcular_puntaje(mano):
    suma = 0
    ases = 0
    for carta in mano:
        val = carta['valor']
        if val in ['J', 'Q', 'K']:
            suma += 10
        elif val == 'A':
            ases += 1
            suma += 11
        else:
            suma += int(val)
            
    while suma > 21 and ases:
        suma -= 10
        ases -= 1
    return suma

@method_decorator(login_required, name='dispatch')
class BlackjackView(View):
    template_name = 'casino/blackjack.html'

    def get(self, request):
        perfil = request.user.perfil
        
        # Inicializar sesión si no existe
        if 'bj_estado' not in request.session:
            request.session['bj_estado'] = 'esperando_apuesta'
            request.session['bj_apuesta'] = 0
            request.session['bj_mano_jugador'] = []
            request.session['bj_mano_dealer'] = []
            
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': request.session.get('bj_estado'),
            'apuesta_actual': request.session.get('bj_apuesta'),
            'mano_jugador': request.session.get('bj_mano_jugador'),
            'mano_dealer': request.session.get('bj_mano_dealer'),
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            'puntaje_dealer': calcular_puntaje(request.session.get('bj_mano_dealer', [])) if request.session.get('bj_estado') == 'terminado' else 0
        }
        
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado': 'Falta plantilla', 'juego': 'Pixel Blackjack'})

    def post(self, request):
        perfil = request.user.perfil
        accion = request.POST.get('accion')
        is_ajax = request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        estado_actual = request.session.get('bj_estado', 'esperando_apuesta')
        
        ganancia = 0
        win = False
        empate = False

        if accion == 'apostar' and estado_actual in ['esperando_apuesta', 'terminado']:
            try:
                monto = int(request.POST.get('monto_apuesta', 0))
                if monto <= 0: raise ValueError
            except ValueError:
                messages.error(request, "Apuesta inválida.")
                return self._responder(request, is_ajax, perfil)
                
            if perfil.fichas < monto:
                messages.error(request, "No tienes fichas suficientes.")
                if is_ajax:
                    mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
                    return JsonResponse({'estado_req': 'error', 'error': 'Saldo insuficiente', 'mensajes': mensajes_list})
                return redirect('casino:blackjack')

            # Iniciar partida
            perfil.fichas -= monto
            perfil.save()
            
            mazo = crear_mazo()
            mano_jugador = [mazo.pop(), mazo.pop()]
            mano_dealer = [mazo.pop(), mazo.pop()]
            
            request.session['bj_mazo'] = mazo
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_apuesta'] = monto
            request.session['bj_estado'] = 'jugando'
            
            # Chequear Blackjack natural del jugador
            if calcular_puntaje(mano_jugador) == 21:
                request.session['bj_estado'] = 'terminado'
                win = True
                ganancia = int(monto * 2.5) # Blackjack paga 3 a 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡BLACKJACK NATURAL! Ganas {ganancia} fichas.")
                
        elif accion == 'pedir' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            
            mano_jugador.append(mazo.pop())
            request.session['bj_mano_jugador'] = mano_jugador
            request.session['bj_mazo'] = mazo
            
            if calcular_puntaje(mano_jugador) > 21:
                request.session['bj_estado'] = 'terminado'
                messages.error(request, "¡Te has pasado de 21! Gana el Dealer.")

        elif accion == 'plantarse' and estado_actual == 'jugando':
            mazo = request.session.get('bj_mazo', [])
            mano_jugador = request.session.get('bj_mano_jugador', [])
            mano_dealer = request.session.get('bj_mano_dealer', [])
            apuesta = request.session.get('bj_apuesta', 0)
            
            puntaje_jugador = calcular_puntaje(mano_jugador)
            puntaje_dealer = calcular_puntaje(mano_dealer)
            
            # Dealer pide hasta 17
            while puntaje_dealer < 17:
                mano_dealer.append(mazo.pop())
                puntaje_dealer = calcular_puntaje(mano_dealer)
                
            request.session['bj_mano_dealer'] = mano_dealer
            request.session['bj_mazo'] = mazo
            request.session['bj_estado'] = 'terminado'
            
            if puntaje_dealer > 21 or puntaje_jugador > puntaje_dealer:
                win = True
                ganancia = apuesta * 2
                perfil.fichas += ganancia
                perfil.save()
                messages.success(request, f"¡Has ganado al Dealer! Te llevas {ganancia} fichas.")
            elif puntaje_jugador == puntaje_dealer:
                empate = True
                ganancia = apuesta # Devuelve la apuesta
                perfil.fichas += ganancia
                perfil.save()
                messages.info(request, "Empate. Recuperas tu apuesta.")
            else:
                messages.error(request, "Gana el Dealer.")

        else:
            messages.error(request, "Acción no válida en este momento.")

        # Guardar la sesión explícitamente porque modificamos listas mutables a veces
        request.session.modified = True
        return self._responder(request, is_ajax, perfil, ganancia=ganancia, win=win, empate=empate)

    def _responder(self, request, is_ajax, perfil, ganancia=0, win=False, empate=False):
        estado_bj = request.session.get('bj_estado')
        mano_dealer = request.session.get('bj_mano_dealer', [])
        
        contexto = {
            'fichas_actuales': perfil.fichas,
            'estado': estado_bj,
            'apuesta_actual': request.session.get('bj_apuesta', 0),
            'mano_jugador': request.session.get('bj_mano_jugador', []),
            'mano_dealer': mano_dealer,
            'puntaje_jugador': calcular_puntaje(request.session.get('bj_mano_jugador', [])),
            # Si se está jugando, oculta el puntaje total del dealer porque una carta está boca abajo
            'puntaje_dealer': calcular_puntaje(mano_dealer) if estado_bj == 'terminado' else 0,
            'ganancia': ganancia,
            'win': win,
            'empate': empate
        }
        
        if is_ajax:
            mensajes_list = [{'tag': m.tags, 'texto': str(m)} for m in messages.get_messages(request)]
            return JsonResponse({
                'estado_req': 'ok',
                'contexto': contexto,
                'mensajes': mensajes_list
            })
            
        try:
            get_template(self.template_name)
            return render(request, self.template_name, contexto)
        except TemplateDoesNotExist:
            return JsonResponse({'estado_req': 'ok', 'contexto': contexto})
