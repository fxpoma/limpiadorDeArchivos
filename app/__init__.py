"""
Aplicación Flask - Inicialización.
Configura la aplicación y registra todos los blueprints.

PERSISTENCIA SIN CONFIGURACIÓN ADICIONAL:
- Valida directorios de datos al inicio
- Configura SQLite con WAL mode para durabilidad
- Detecta y crea estructura de datos automáticamente
"""
from flask import Flask, render_template, request, g
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import time
import os
import sys

# Importar configuración
from config import Config, ensure_data_directories, validate_persistence, get_db_path


def create_app():
    """
    Crea y configura la aplicación Flask.
    
    Returns:
        Flask: Aplicación configurada
    """
    # Obtener la ruta base del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    # Cargar configuración
    app.config.from_object(Config)
    
    # ==================== INICIALIZACIÓN DE PERSISTENCIA ====================
    
    print("=" * 50)
    print("Inicializando persistencia...")
    print(f"  Entorno: {'Docker' if Config.IN_DOCKER else 'Local'}")
    print(f"  Directorio de datos: {Config.DATA_DIR}")
    print(f"  Base de datos: {Config.DB_PATH}")
    
    # 1. Asegurar que existan todos los directorios necesarios
    try:
        ensure_data_directories()
        print("  ✓ Directorios de datos verificados/creados")
    except Exception as e:
        print(f"  ✗ Error al crear directorios: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 2. Validar que los directorios sean accesibles
    persistence_status = validate_persistence()
    all_ok = all(persistence_status.values())
    
    if all_ok:
        print("  ✓ Persistencia validada correctamente")
    else:
        print("  ⚠ Advertencia: Algunos directorios no están disponibles:")
        for key, value in persistence_status.items():
            if not value:
                print(f"    - {key}: no disponible o sin permisos de escritura")
        
        # En modo no-Docker, crear los directorios que faltan
        if not Config.IN_DOCKER:
            print("  Intentando crear directorios faltantes...")
            try:
                ensure_data_directories()
                persistence_status = validate_persistence()
                if all(persistence_status.values()):
                    print("  ✓ Directorios creados exitosamente")
                else:
                    print("  ✗ No se pudieron crear todos los directorios", file=sys.stderr)
                    sys.exit(1)
            except Exception as e:
                print(f"  ✗ Error: {e}", file=sys.stderr)
                sys.exit(1)
    
    print("=" * 50)
    
    # 3. Configurar SQLite con WAL mode para mayor durabilidad
    # Esto se hace después de que los directorios existan
    import sqlite3
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        # Habilitar WAL mode para mejor rendimiento y durabilidad
        conn.execute('PRAGMA journal_mode=WAL')
        # Asegurar que las transacciones sean durables
        conn.execute('PRAGMA synchronous=FULL')
        conn.close()
        print("  ✓ SQLite configurado con WAL mode")
    except Exception as e:
        print(f"  ⚠ Advertencia: No se pudo configurar WAL mode: {e}")
    
    # Inicializar extensiones
    bcrypt = Bcrypt(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Actualizado para Blueprint
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    
    # Crear directorios necesarios (para static en el contenedor)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CODES_FOLDER'], exist_ok=True)
    
    # Importar modelos y servicios
    from app.models import create_tables, load_user, get_db_connection
    from app.services import is_ip_blocked, record_request, update_route_stats
    from app.models.user import User
    
    # Configurar login_manager
    @login_manager.user_loader
    def load_user_callback(user_id):
        return load_user(user_id)
    
    # ==================== MIDDLEWARE ====================
    
    @app.before_request
    def before_request():
        """Middleware que se ejecuta antes de cada request"""
        g.start_time = time.time()
        
        # Verificar si la IP está bloqueada
        from flask import jsonify
        ip = request.remote_addr
        if is_ip_blocked(ip):
            return jsonify({'success': False, 'error': 'Tu IP ha sido bloqueada. Contacta al administrador.'}), 403
    
    @app.after_request
    def after_request(response):
        """Middleware que se ejecuta después de cada request"""
        # Calcular tiempo de respuesta
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
        else:
            response_time = 0
        
        # No registrar requests estáticos
        if not request.path.startswith('/static/'):
            from flask_login import current_user
            user_id = None
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                user_id = current_user.id
            
            # Registrar la consulta
            record_request(
                user_id=user_id,
                ip_address=request.remote_addr,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                response_time=response_time,
                user_agent=request.headers.get('User-Agent'),
                referer=request.headers.get('Referer')
            )
            
            # Actualizar estadísticas de la ruta
            update_route_stats(request.path, request.method, response_time, request.remote_addr)
        
        return response
    
    # ==================== REGISTRAR BLUEPRINTS ====================
    
    # Rutas principales
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.codes import bp as codes_bp
    from app.routes.files import bp as files_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(codes_bp)
    app.register_blueprint(files_bp)
    
    # Rutas de admin
    from app.routes.admin.users import bp as admin_users_bp
    from app.routes.admin.codes import bp as admin_codes_bp
    from app.routes.admin.modules import bp as admin_modules_bp
    from app.routes.admin.stats import bp as admin_stats_bp
    from app.routes.admin.requests import bp as admin_requests_bp
    from app.routes.admin.backup import bp as admin_backup_bp
    
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_codes_bp)
    app.register_blueprint(admin_modules_bp)
    app.register_blueprint(admin_stats_bp)
    app.register_blueprint(admin_requests_bp)
    app.register_blueprint(admin_backup_bp)
    
    # Rutas de API
    from app.routes.api.stats import bp as api_stats_bp
    app.register_blueprint(api_stats_bp)
    
    # Crear tablas de base de datos
    create_tables()
    
    return app
