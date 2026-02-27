"""
Rutas de la aplicación.
Contiene todos los blueprints de rutas.
"""
from flask import Blueprint

# Crear blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
codes_bp = Blueprint('codes', __name__)
files_bp = Blueprint('files', __name__)

# Importar rutas para registrar los decorators
from app.routes import auth, main, codes, files

# Rutas de admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
from app.routes.admin import users, codes as admin_codes, modules, stats, requests
