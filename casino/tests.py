from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Perfil, PaqueteFichas
from datetime import timedelta
from decimal import Decimal

class CasinoLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.paquete = PaqueteFichas.objects.create(
            nombre="Pack 100",
            cantidad_fichas=100,
            precio_dinero_ficticio=50.00
        )

    def test_perfil_creado_automaticamente(self):
        """Verifica que se cree un perfil al crear un usuario."""
        self.assertIsNotNone(self.user.perfil)
        self.assertEqual(self.user.perfil.dinero_ficticio, 1000.00)

    def test_recompensa_diaria(self):
        """Verifica la lógica de recompensa diaria en la PortadaView."""
        perfil = self.user.perfil
        # Simular que la última recarga fue hace más de 24 horas
        perfil.ultima_recarga = timezone.now() - timedelta(days=1, seconds=1)
        perfil.save()

        self.client.login(username='testuser', password='password123')
        response = self.client.get('/casino/')
        
        perfil.refresh_from_db()
        self.assertEqual(perfil.dinero_ficticio, 1500.00)

    def test_compra_fichas_exito(self):
        """Verifica que una compra exitosa descuenta dinero y suma fichas."""
        self.client.login(username='testuser', password='password123')
        # Añadir al carrito
        self.client.post(f'/casino/carrito/añadir/{self.paquete.id}/', follow=True)
        # Procesar compra
        self.client.post('/casino/carrito/comprar/', follow=True)
        
        perfil = self.user.perfil
        perfil.refresh_from_db()
        
        self.assertEqual(perfil.dinero_ficticio, Decimal('950.00'))
        self.assertEqual(perfil.fichas, 100)

    def test_compra_fichas_insuficiente(self):
        """Verifica que no se puede comprar sin saldo suficiente."""
        perfil = self.user.perfil
        perfil.dinero_ficticio = 10.00
        perfil.save()

        self.client.login(username='testuser', password='password123')
        self.client.post(f'/casino/carrito/añadir/{self.paquete.id}/')
        response = self.client.post('/casino/carrito/comprar/')
        
        perfil.refresh_from_db()
        self.assertEqual(perfil.dinero_ficticio, 10.00)
        self.assertEqual(perfil.fichas, 0)

class RuletaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.perfil.fichas = 100
        self.user.perfil.save()

    def test_ruleta_get(self):
        """Verifica que la vista de la ruleta cargue correctamente."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/casino/ruleta/')
        self.assertEqual(response.status_code, 200)

    def test_ruleta_apuesta_sin_fichas(self):
        """Verifica que no se puede apostar si no hay fichas suficientes."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/ruleta/', {
            'tipo_apuesta': 'color',
            'color': 'rojo',
            'monto': 200 # Tiene 100
        })
        self.user.perfil.refresh_from_db()
        self.assertEqual(self.user.perfil.fichas, 100) # No se cobró
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('No tienes suficientes fichas para esta apuesta.', form.non_field_errors())

    def test_ruleta_apuesta_invalida(self):
        """Verifica validaciones del formulario (ej. faltan campos)."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/ruleta/', {
            'tipo_apuesta': 'numero',
            'monto': 10
        })
        form = response.context['form']
        self.assertIn('numero', form.errors)

    def test_ruleta_apuesta_valida(self):
        """Verifica que se descuenten las fichas tras una apuesta válida."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/ruleta/', {
            'tipo_apuesta': 'numero',
            'numero': 15,
            'monto': 10
        })
        self.user.perfil.refresh_from_db()
        # Pueden ser 90 (perdió) o 90 + 350 (ganó). Como hay random, solo probaremos si cambió o si la respuesta es correcta.
        self.assertNotEqual(self.user.perfil.fichas, 100) # Se debieron descontar al menos

class TragaperrasTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.perfil.fichas = 50
        self.user.perfil.save()

    def test_slots_get(self):
        """Verifica que la tragaperras cargue correctamente."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/casino/slots/')
        self.assertEqual(response.status_code, 200)

    def test_slots_apuesta_sin_fichas(self):
        """Verifica que no se puede jugar sin 10 fichas."""
        self.user.perfil.fichas = 5
        self.user.perfil.save()
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/slots/')
        self.user.perfil.refresh_from_db()
        self.assertEqual(self.user.perfil.fichas, 5) # No se cobró
        # El mensaje de error se verifica en messages, no en form
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "No tienes fichas suficientes. ¡Ve a la tienda a recargar!")

    def test_slots_apuesta_valida(self):
        """Verifica el descuento de la apuesta al jugar a las slots."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/slots/')
        self.user.perfil.refresh_from_db()
        
        # Cobró 10 fichas. Puede ganar 10 (empate), 20+ (ganancia) o perder (40 fichas).
        self.assertIn(self.user.perfil.fichas, [40, 50, 60, 70, 90, 140, 540, 1040])
        self.assertTrue('resultado' in response.context)
        self.assertEqual(len(response.context['resultado']), 3)

class RavynGridTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.perfil.fichas = 100
        self.user.perfil.save()

    def test_ravyn_get(self):
        """Verifica que el Ravyn Grid cargue correctamente."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/casino/ravyn/')
        self.assertEqual(response.status_code, 200)

    def test_ravyn_apuesta_sin_fichas(self):
        """Verifica que no se puede jugar sin fichas suficientes para la apuesta elegida."""
        self.user.perfil.fichas = 10
        self.user.perfil.save()
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/ravyn/', {'monto_apuesta': 20})
        self.user.perfil.refresh_from_db()
        self.assertEqual(self.user.perfil.fichas, 10) # No se cobró
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "No tienes fichas suficientes. ¡Ve a la tienda a recargar!")

    def test_ravyn_apuesta_valida(self):
        """Verifica el descuento de la apuesta al jugar a Ravyn Grid con un monto personalizado."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/casino/ravyn/', {'monto_apuesta': 30})
        self.user.perfil.refresh_from_db()
        
        # Cobró 30 fichas. Pudo haber ganado o perdido.
        self.assertNotEqual(self.user.perfil.fichas, 100)
        self.assertTrue('resultado' in response.context)
        self.assertEqual(len(response.context['resultado']), 9)

class BlackjackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.perfil.fichas = 100
        self.user.perfil.save()

    def test_blackjack_get(self):
        """Verifica que el juego de Blackjack inicie correctamente el estado."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/casino/blackjack/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('bj_estado'), 'esperando_apuesta')

    def test_blackjack_apostar(self):
        """Verifica que hacer una apuesta inicie la partida y descuente las fichas."""
        self.client.login(username='testuser', password='password123')
        # Iniciar sesión primero
        self.client.get('/casino/blackjack/')
        
        # Apostar
        response = self.client.post('/casino/blackjack/', {'accion': 'apostar', 'monto_apuesta': 20})
        
        # Verificar estado
        self.assertIn(self.client.session.get('bj_estado'), ['jugando', 'terminado']) # Puede terminar si hace Blackjack natural
        self.assertEqual(self.client.session.get('bj_apuesta'), 20)
        
        self.user.perfil.refresh_from_db()
        self.assertNotEqual(self.user.perfil.fichas, 100) # Se debieron descontar (y tal vez sumar si hay BJ natural)

