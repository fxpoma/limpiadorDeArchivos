# Plan de Refactorización del Proyecto

## Objetivo

Separar el archivo `app.py` (50,000+ caracteres) en módulos más pequeños y mantenibles, facilitando la comprensión del código por parte de una IA y permitiendo modificaciones más eficientes.

---

## Estructura Propuesta

```
limpiadorDeArchivos/
├── app.py                    # Punto de entrada, configuración básica
├── config.py                 # Configuración de la aplicación
├── requirements.txt
├── Dockerfile
├── dokploy.yaml
├── start.sh
├── .gitignore
├── .env.example
├── README.md
├── PLATFORM_INDEX.md         # ← Archivo de indexación para IA
│
├── app/
│   ├── __init__.py          # Inicialización de la aplicación Flask
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # Modelo de usuario y autenticación
│   │   ├── database.py      # Conexión a BD y tablas
│   │   ├── code.py          # Modelo de códigos de procesamiento
│   │   ├── stats.py         # Modelos de estadísticas
│   │   └── security.py      # Modelos de seguridad (bloqueo IP)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # login, register, logout
│   │   ├── main.py          # index, profile
│   │   ├── codes.py         # manage_codes, edit_code, delete_code
│   │   ├── files.py         # upload, process, download, cleanup
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── users.py     # admin_users, approve_user, delete_user
│   │   │   ├── codes.py     # admin_codes, admin_view_code
│   │   │   ├── modules.py   # manage_modules, install_module
│   │   │   ├── stats.py     # admin_stats
│   │   │   ├── requests.py  # admin_request_stats, blocked_ips
│   │   │   └── security.py  # block_ip, unblock_ip
│   │   │
│   │   └── api/
│   │       ├── __init__.py
│   │       └── stats.py     # API de estadísticas JSON
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stats_service.py # Funciones de registro de estadísticas
│   │   ├── security_service.py # Funciones de seguridad
│   │   ├── file_service.py # Lógica de procesamiento de archivos
│   │   └── module_service.py # Instalación de módulos
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py     # Validaciones de entrada
│       └── helpers.py       # Funciones helper
│
├── templates/                 # Templates HTML (sin cambios)
├── static/                   # Archivos estáticos
└── data/                     # Base de datos (en volumen Docker)
```

---

## Pasos de Implementación

### 1. Crear estructura de carpetas

```bash
mkdir -p app/models app/routes/admin app/routes/api app/services app/utils
```

### 2. Crear archivo de indexación (`PLATFORM_INDEX.md`)

Documentación completa que explica:

- Estructura del proyecto
- Cómo hacer modificaciones
- Convenciones de código
- Rutas disponibles
- Base de datos

### 3. Migrar código existente

#### Paso 3.1: Crear `config.py`

- Configuración de Flask
- Variables de entorno

#### Paso 3.2: Crear `app/models/`

- `user.py`: Clase User, load_user
- `database.py`: get_db_connection, create_tables
- `code.py`: Modelos de códigos
- `stats.py`: Modelos de estadísticas
- `security.py`: Modelos de seguridad

#### Paso 3.3: Crear `app/services/`

- `stats_service.py`: record_activity, update_user_stats, update_daily_stats, record_request, update_route_stats
- `security_service.py`: is_ip_blocked, block_ip
- `file_service.py`: Lógica de procesamiento
- `module_service.py`: Instalación de módulos

#### Paso 3.4: Crear `app/routes/`

- `auth.py`: Rutas de autenticación
- `main.py`: Rutas principales
- `codes.py`: Gestión de códigos
- `files.py`: Procesamiento de archivos
- `admin/users.py`: Administración de usuarios
- `admin/stats.py`: Estadísticas
- `admin/requests.py`: Estadísticas de requests

#### Paso 3.5: Actualizar `app/__init__.py` y `app.py`

- Importar todos los módulos
- Registrar blueprints

---

## Archivo de Indexación (`PLATFORM_INDEX.md`)

### Contenido sugerido

```markdown
# Platform Index - Limpiador de Archivos

## Estructura del Proyecto
[Descripción de carpetas y archivos]

## Base de Datos
[Esquema de tablas]

## Rutas Disponibles
| Método | Ruta | Descripción | Requiere Auth |
|--------|------|-------------|----------------|
| GET | / | Página principal | No |
| GET/POST | /login | Iniciar sesión | No |
| ...

## Cómo Agregar Nueva Ruta
1. Crear archivo en app/routes/
2. Definir blueprint
3. Importar en app/__init__.py
4. Registrar blueprint

## Cómo Agregar Nueva Tabla
1. Agregar CREATE TABLE en app/models/database.py
2. Ejecutar migración
3. Agregar modelo si es necesario

## Convenciones
- Usar inglés para nombres de variables
- Usar español para mensajes de usuario
- Prefijo "admin_" para rutas de administración
- Prefijo "api_" para rutas de API
```

---

## Orden para IA (Instructions for AI)

```markdown
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
3. Add migration script if table already exists

### Adding New Model
1. Create file in `app/models/`
2. Define class with SQLAlchemy or raw SQL
3. Import in `app/models/__init__.py`

### Adding New Service
1. Create file in `app/services/`
2. Define functions
3. Import where needed

### Testing
Run: `python -m py_compile app.py`
Start server: `python app.py`
```

---

## Tiempo Estimado

- Crear estructura: 30 min
- Migrar modelos: 1 hora
- Migrar servicios: 1 hora
- Migrar rutas: 2 horas
- Crear indexación: 30 min
- **Total: ~5 horas**

---

## Recomendaciones

1. **Hacer cambios incrementales**: No refactorizar todo de una vez
2. **Mantener backward compatibility**:新旧共存 durante transición
3. **Probar frecuentemente**: Ejecutar después de cada módulo
4. **Documentar decisiones**: Agregar comentarios en código
5. **Actualizar PLATFORM_INDEX.md**: Con cada cambio significativo
