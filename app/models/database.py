"""
Funciones de base de datos para la aplicación.
Maneja la conexión y la creación de tablas.
"""
import sqlite3
import os
from config import get_db_path


def get_db_connection():
    """
    Obtiene una conexión a la base de datos SQLite.
    Retorna un objeto de conexión con row_factory establecido.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """
    Crea todas las tablas necesarias para la aplicación.
    Utiliza CREATE TABLE IF NOT EXISTS para retrocompatibilidad.
    """
    conn = get_db_connection()
    
    # Crear tabla de usuarios si no existe
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar columna is_admin si no existe (para bases de datos existentes)
    try:
        conn.execute('SELECT is_admin FROM users LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
    
    # Agregar columna status si no existe (para bases de datos existentes)
    try:
        conn.execute('SELECT status FROM users LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'pending'")
    
    # Tabla de códigos de procesamiento
    conn.execute('''
        CREATE TABLE IF NOT EXISTS processing_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            code TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabla de módulos Python instalados
    conn.execute('''
        CREATE TABLE IF NOT EXISTS python_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT UNIQUE NOT NULL,
            installed_by INTEGER,
            installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ==================== TABLAS DE ESTADÍSTICAS ====================
    # Tabla de estadísticas generales del sistema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_type TEXT NOT NULL,
            stat_value INTEGER DEFAULT 0,
            stat_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de logs de actividad
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabla de estadísticas de uso por usuario
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            login_count INTEGER DEFAULT 0,
            file_processed_count INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabla de estadísticas diarias
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date DATE DEFAULT CURRENT_DATE,
            page_views INTEGER DEFAULT 0,
            unique_visitors INTEGER DEFAULT 0,
            logins INTEGER DEFAULT 0,
            file_processing INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de logs de requests
    conn.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip_address TEXT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER,
            response_time REAL,
            user_agent TEXT,
            referer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabla de estadísticas de rutas específicas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS route_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT NOT NULL,
            method TEXT NOT NULL,
            hit_count INTEGER DEFAULT 0,
            unique_visitors INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de IPs bloqueadas por seguridad
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blocked_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            reason TEXT,
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_permanent INTEGER DEFAULT 0
        )
    ''')
    
    # Verificar y crear tabla user_stats si no existe
    try:
        conn.execute('SELECT login_count FROM user_stats LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_count INTEGER DEFAULT 0,
                file_processed_count INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                last_activity TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    
    # Verificar y crear tabla daily_stats si no existe
    try:
        conn.execute('SELECT page_views FROM daily_stats LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date DATE DEFAULT CURRENT_DATE,
                page_views INTEGER DEFAULT 0,
                unique_visitors INTEGER DEFAULT 0,
                logins INTEGER DEFAULT 0,
                file_processing INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()
