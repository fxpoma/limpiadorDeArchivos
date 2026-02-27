"""
Configuración de la aplicación Flask.
Carga variables de entorno y define configuraciones globales.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()


class Config:
    """Configuración base de la aplicación"""
    
    # Obtener la ruta base del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Detectar si está en Docker
    IN_DOCKER = os.path.exists('/.dockerenv') or os.getenv('IN_DOCKER', 'false').lower() == 'true'
    
    # Configuración de Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu-clave-secreta-aqui')
    
    # Rutas de archivos (absolutas)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv('UPLOAD_FOLDER', 'static/uploads'))
    CODES_FOLDER = os.path.join(BASE_DIR, os.getenv('CODES_FOLDER', 'static/codes'))
    
    # Límites
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Puerto
    PORT = int(os.getenv('FLASK_RUN_PORT', 5000))
    
    # Configuración de debug
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Directorio de la base de datos (siempre /app/data para compatibilidad con Docker)
    DB_DIR = '/app/data'
    DB_PATH = os.path.join(DB_DIR, 'database.db')


def get_db_path():
    """Obtiene la ruta de la base de datos, creando el directorio si es necesario"""
    os.makedirs(Config.DB_DIR, exist_ok=True)
    return Config.DB_PATH
