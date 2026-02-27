"""
Rutas de administración.
Blueprint para todas las rutas de admin.
"""
from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Importar después de definir bp para evitar importación circular
from app.routes import admin
