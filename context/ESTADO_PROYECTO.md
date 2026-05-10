# **Documentación Técnica - Retro Casino**

Este documento detalla la estructura, funcionalidades y el estado actual del proyecto desarrollado siguiendo las instrucciones incrementales.

## **1. Estructura del Proyecto**

```text
PRACTICATEMA4/
├── config/                 # Configuración principal de Django
│   ├── settings.py         # Ajustes (Apps, DB, Templates, Static)
│   └── urls.py             # Enrutamiento raíz (admin/ y casino/)
├── casino/                 # Aplicación principal del casino
│   ├── migrations/         # Historial de base de datos
│   ├── static/             # Archivos estáticos (CSS, Imágenes)
│   ├── admin.py            # Configuración del panel de administración
│   ├── apps.py             # Configuración de la app y carga de signals
│   ├── cart.py             # Lógica de gestión del carrito (Sesiones)
│   ├── models.py           # Definición de Perfil y PaqueteFichas
│   ├── signals.py          # Creación automática de Perfil al crear User
│   ├── urls.py             # Rutas de la aplicación (tienda, carrito, portada)
│   └── views.py            # Lógica de negocio y vistas (CBVs)
├── context/                # Documentación y guías del proyecto
│   ├── AGENT_INSTRUCTIONS.md
│   ├── ESTADO_PROYECTO.md  # (Este archivo)
│   └── PLAN_IMPLEMENTACION.md
├── templates/              # Plantillas HTML globales
│   ├── base.html           # Layout base con diseño Pixel Art
│   └── casino/             # Plantillas específicas de la app
│       ├── portada.html    # Lobby principal
│       └── tienda.html     # Tienda y resumen del carrito
├── venv/                   # Entorno virtual (Python 3.14.3)
├── db.sqlite3              # Base de datos local
├── manage.py               # Utilidad de comandos de Django
├── requirements.txt        # Dependencias del proyecto
└── seed.py                 # Script de carga de datos iniciales
```

---

## **2. Funcionalidades Principales**

### **A. Sistema de Usuarios y Perfiles**
*   **Modelo Perfil:** Extiende al usuario de Django para almacenar `dinero_ficticio` (empezando con 1000.00) y `fichas`.
*   **Signals:** Cada vez que se crea un usuario (vía Admin o Registro), se genera automáticamente su perfil asociado.

### **B. Tienda y Carrito de Compras**
*   **Carrito:** Clase personalizada en `cart.py` que utiliza las sesiones de Django para persistir la selección del usuario sin necesidad de base de datos temporal.
*   **Compra:** Valida si el usuario tiene saldo suficiente de `dinero_ficticio`. Si es así, descuenta el dinero, suma las fichas al `Perfil` y vacía el carrito.
*   **Respaldo JSON:** Las vistas de Tienda y Portada devuelven un JSON con la información si por algún motivo las plantillas `.html` no se encuentran.

### **C. Recompensa Diaria**
*   **Lógica de Fidelización:** Al acceder a la Portada, el sistema verifica el campo `ultima_recarga`. Si han pasado más de 24 horas, se le otorgan **500 monedas** automáticamente.

### **D. Interfaz Visual (Pixel Art)**
*   **Estética Retro:** Uso de la fuente **Press Start 2P**.
*   **CSS Custom:** Bordes "escalonados" de 4px, renderizado pixelado de imágenes y paleta de colores vibrantes (Neon/Dark).

---

## **3. Módulos y sus Funciones**

| Módulo | Función |
| :--- | :--- |
| `models.py` | Define `PaqueteFichas` (productos) y `Perfil` (cartera del usuario). |
| `views.py` | Gestiona la lógica de la tienda, la portada y el procesamiento de pagos. |
| `cart.py` | Encapsula la lógica de añadir/quitar productos del carrito de sesión. |
| `signals.py` | Asegura la integridad de la relación 1:1 entre `User` y `Perfil`. |
| `admin.py` | Permite gestionar usuarios y crear nuevos paquetes de fichas. |
| `seed.py` | Permite poblar la base de datos con datos de prueba rápidamente. |

---

## **4. Estado Actual del Proyecto**

*   **Fases Completadas:** 6 de 6.
*   **Base de Datos:** Migrada y con datos iniciales (vía seed.py).
*   **Usuario Admin:** Creado (`admin` / `admin`).
*   **Compatibilidad:** Se aplicó un parche manual en la librería `django/template/context.py` dentro del `venv` para asegurar el funcionamiento estable en **Python 3.14**.

---

## **5. Comandos Útiles**

*   **Cargar datos de prueba:** `.\venv\Scripts\python.exe seed.py`
*   **Ejecutar Servidor:** `.\venv\Scripts\python.exe manage.py runserver`
*   **Crear nuevo Superusuario:** `.\venv\Scripts\python.exe manage.py createsuperuser`
