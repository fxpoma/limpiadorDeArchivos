"""
Configuración de la aplicación Flask.
Carga variables de entorno y define configuraciones globales.

PERSISTENCIA SIN CONFIGURACIÓN ADICIONAL:
- Detecta automáticamente el entorno (Docker/local)
- Usa rutas dinámicas para datos según el entorno
- Valida y crea estructuras de directorios automáticamente
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
    
    # ==================== PERSISTENCIA AUTOMÁTICA ====================
    # Determinar directorio de datos según el entorno
    if IN_DOCKER:
        # En Docker: usar /app/data que se monta como volumen
        DATA_DIR = '/app/data'
    else:
        # En local: usar directorio ./data en la raíz del proyecto
        DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # Rutas de archivos (absolutas) - todas dentro de DATA_DIR
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    CODES_FOLDER = os.path.join(BASE_DIR, 'static/codes')
    
    # Base de datos siempre en DATA_DIR para persistencia
    DB_DIR = DATA_DIR
    DB_PATH = os.path.join(DB_DIR, 'database.db')
    
    # Backups también en DATA_DIR
    BACKUP_DIR = os.path.join(DB_DIR, 'backups')
    
    # Límites
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Puerto
    PORT = int(os.getenv('FLASK_RUN_PORT', 5000))
    
    # Configuración de debug
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'


def get_db_path():
    """
    Obtiene la ruta de la base de datos, creando el directorio si es necesario.
    
    Esta función asegura persistencia sin configuración adicional:
    - Crea el directorio de datos si no existe
    - Usa la ruta correcta según el entorno (Docker/local)
    """
    os.makedirs(Config.DB_DIR, exist_ok=True)
    return Config.DB_PATH


def ensure_data_directories():
    """
    Asegura que todos los directorios de datos existan.
    
    Debe llamarse al inicio de la aplicación para garantizar
    que los volúmenes estén correctamente inicializados.
    """
    directories = [
        Config.DB_DIR,
        Config.BACKUP_DIR,
        Config.UPLOAD_FOLDER,
        Config.CODES_FOLDER
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    return True


def validate_persistence():
    """
    Valida que los directorios de persistencia estén accesibles y tengan permisos.
    
    Returns:
        dict: Estado de cada directorio
    """
    results = {
        'db_dir': False,
        'backup_dir': False,
        'uploads_dir': False,
        'codes_dir': False
    }
    
    try:
        # Verificar directorio de base de datos
        results['db_dir'] = os.path.exists(Config.DB_DIR) and os.access(Config.DB_DIR, os.W_OK)
        
        # Verificar directorio de backups
        results['backup_dir'] = os.path.exists(Config.BACKUP_DIR) and os.access(Config.BACKUP_DIR, os.W_OK)
        
        # Verificar directorio de uploads
        results['uploads_dir'] = os.path.exists(Config.UPLOAD_FOLDER) and os.access(Config.UPLOAD_FOLDER, os.W_OK)
        
        # Verificar directorio de códigos
        results['codes_dir'] = os.path.exists(Config.CODES_FOLDER) and os.access(Config.CODES_FOLDER, os.W_OK)
        
    except Exception as e:
        print(f"Error validando directorios de persistencia: {e}")
    
    return results
