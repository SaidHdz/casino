import os
import django
import sys

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from casino.models import PaqueteFichas

def seed_data():
    print("Iniciando carga de datos...")
    
    paquetes = [
        {
            'nombre': 'Bolsa de Principiante',
            'descripcion': 'Ideal para empezar a probar suerte.',
            'cantidad_fichas': 100,
            'precio_dinero_ficticio': 50.00
        },
        {
            'nombre': 'Cofre del Apostador',
            'descripcion': 'El paquete más popular entre nuestros clientes.',
            'cantidad_fichas': 500,
            'precio_dinero_ficticio': 200.00
        },
        {
            'nombre': 'Saco de Oro Pixelado',
            'descripcion': 'Para aquellos que van en serio.',
            'cantidad_fichas': 1500,
            'precio_dinero_ficticio': 500.00
        },
        {
            'nombre': 'Caja Fuerte VIP',
            'descripcion': 'Solo para los grandes magnates del casino.',
            'cantidad_fichas': 5000,
            'precio_dinero_ficticio': 1500.00
        }
    ]

    for p in paquetes:
        obj, created = PaqueteFichas.objects.get_or_create(
            nombre=p['nombre'],
            defaults=p
        )
        if created:
            print(f"Creado: {p['nombre']}")
        else:
            print(f"Ya existía: {p['nombre']}")

    print("Carga de datos completada con éxito.")

if __name__ == '__main__':
    seed_data()
