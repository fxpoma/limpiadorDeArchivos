# Platform Index - Limpiador de Archivos

## Estructura del Proyecto

```
limpiadorDeArchivos/
├── app.py                    # Punto de entrada de la aplicación
├── config.py                 # Configuración de la aplicación
├── requirements.txt          # Dependencias Python
├── Dockerfile                # Imagen Docker
├── dokploy.yaml              # Configuración Dokploy
├── start.sh                  # Script de inicio
├── .gitignore
├── .env.example
├── README.md
├── PLATFORM_INDEX.md         # Este archivo
│
├── app/                      # Paquete principal
│   ├── __init__.py          # Inicialización de Flask
│   │
│   ├── models/              # Modelos de datos
│   │   ├── __init__.py
│   │   ├── database.py      # Conexión a BD y tablas
│   │   └── user.py          # Modelo de usuario
│   │
│   ├── routes/              # Rutas de la aplicación
│   │   ├── __init__.py
│   │   ├── auth.py          # login, register, logout
│   │   ├── main.py          # index, profile
│   │   ├── codes.py         # manage_codes, edit_code, delete_code
│   │   ├── files.py         # upload, process, download, cleanup
│   │   ├── admin/
│   │   │   ├── users.py    # admin_users, approve_user, delete_user
│   │   │   ├── codes.py    # admin_codes, admin_view_code
│   │   │   ├── modules.py  # manage_modules, install_module
│   │   │   ├── stats.py    # admin_stats
│   │   │   └── requests.py # admin_request_stats, blocked_ips
│   │   └── api/
│   │       └── stats.py    # API de estadísticas JSON
│   │
│   ├── services/            # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── stats_service.py  # Estadísticas
│   │   └── security_service.py # Seguridad
│   │
│   └── utils/              # Utilidades
│       ├── __init__.py
│       ├── validators.py   # Validaciones
│       └── helpers.py     # Funciones helper
│
├── templates/               # Templates HTML
├── static/                  # Archivos estáticos
└── data/                    # Base de datos (en volumen Docker)
```

## Base de Datos

### Tablas Principales

| Tabla | Descripción |
|-------|-------------|
| `users` | Usuarios del sistema |
| `processing_codes` | Códigos de procesamiento |
| `python_modules` | Módulos Python instalados |
| `activity_logs` | Logs de actividad |
| `user_stats` | Estadísticas por usuario |
| `daily_stats` | Estadísticas diarias |
| `request_logs` | Logs de requests HTTP |
| `route_stats` | Estadísticas de rutas |
| `blocked_ips` | IPs bloqueadas |

## Rutas Disponibles

### Rutas Públicas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Página principal |
| GET/POST | `/login` | Iniciar sesión |
| GET/POST | `/register` | Registrar usuario |

### Rutas de Usuario (Requiere Auth)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/logout` | Cerrar sesión |
| GET | `/profile` | Perfil de usuario |
| GET/POST | `/manage_codes` | Gestionar códigos |
| GET | `/edit_code/<id>` | Editar código |
| GET | `/delete_code/<id>` | Eliminar código |
| POST | `/upload` | Subir archivo |
| POST | `/process` | Procesar archivo |
| GET | `/download/<filename>` | Descargar archivo |
| POST | `/cleanup` | Limpiar archivos |
| GET/POST | `/change_password` | Cambiar contraseña |

### Rutas de Admin

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/admin_users` | Ver usuarios |
| GET | `/approve_user/<id>` | Aprobar usuario |
| GET | `/reject_user/<id>` | Rechazar usuario |
| GET | `/delete_user/<id>` | Eliminar usuario |
| GET/POST | `/edit_user/<id>` | Editar usuario |
| GET | `/make_admin/<id>` | Hacer admin |
| GET | `/remove_admin/<id>` | Quitar admin |
| GET | `/admin_codes` | Ver todos los códigos |
| GET | `/admin_delete_code/<id>` | Eliminar código |
| GET | `/admin_view_code/<id>` | Ver código |
| GET | `/manage_modules` | Gestionar módulos |
| POST | `/install_module` | Instalar módulo |
| GET | `/uninstall_module/<name>` | Desinstalar módulo |
| GET | `/admin_stats` | Dashboard de estadísticas |
| GET | `/admin_request_stats` | Estadísticas de requests |
| GET | `/admin_blocked_ips` | Ver IPs bloqueadas |
| POST | `/admin_block_ip` | Bloquear IP |
| GET | `/admin_unblock_ip/<ip>` | Desbloquear IP |

### Rutas de API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/stats/summary` | Resumen de estadísticas |
| GET | `/api/request_stats` | Estadísticas de requests |

## AI INSTRUCTIONS

When modifying this project, follow these rules:

### Adding New Route

1. Create new file in `app/routes/` or existing appropriate file
2. Use Blueprint: `bp = Blueprint('name', __name__)`
3. Add route with decorators: `@bp.route('/path')`
4. Import and register in `app/__init__.py`

### Adding New Database Table

1. Add CREATE TABLE in `app/models/database.py` in `create_tables()` function
2. Use IF NOT EXISTS for backward compatibility
3. The table will be created automatically on next app start

### Adding New Model

1. Create file in `app/models/`
2. Define functions or classes
3. Import in `app/models/__init__.py`

### Adding New Service

1. Create file in `app/services/`
2. Define functions
3. Import in `app/services/__init__.py`

### Testing

Run: `python -m py_compile app.py`
Start server: `python app.py`

## Convenciones

- Usar inglés para nombres de variables
- Usar español para mensajes de usuario
- Prefijo "admin_" para rutas de administración
- Prefijo "api_" para rutas de API
- Usar Blueprint para organizar rutas
- Mantener retrocompatibilidad con la estructura anterior
