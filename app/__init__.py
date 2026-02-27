"""
Aplicación Flask - Inicialización.
Configura la aplicación y registra todos los blueprints.
"""
from flask import Flask, render_template, request, g
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import time
import os

# Importar configuración
from config import Config


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
    
    # Inicializar extensiones
    bcrypt = Bcrypt(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Actualizado para Blueprint
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    
    # Crear directorios necesarios
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
    
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_codes_bp)
    app.register_blueprint(admin_modules_bp)
    app.register_blueprint(admin_stats_bp)
    app.register_blueprint(admin_requests_bp)
    
    # Rutas de API
    from app.routes.api.stats import bp as api_stats_bp
    app.register_blueprint(api_stats_bp)
    
    # Crear tablas de base de datos
    create_tables()
    
    return app
