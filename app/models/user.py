"""
Modelo de usuario y autenticación.
Define la clase User para Flask-Login.
"""
from flask_login import UserMixin
from app.models.database import get_db_connection


class User(UserMixin):
    """
    Clase de usuario para Flask-Login.
    Representa un usuario del sistema con sus atributos.
    """
    def __init__(self, id, username, email, password, is_admin=0, status='pending'):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.status = status


def load_user(user_id):
    """
    Función para cargar un usuario desde la base de datos.
    Utilizada por Flask-Login para recuperar la sesión del usuario.
    
    Args:
        user_id: ID del usuario a cargar
        
    Returns:
        User: Objeto de usuario si existe, None si no existe
    """
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        is_admin = 0
        status = 'pending'
        try:
            is_admin = user['is_admin']
        except:
            pass
        try:
            status = user['status']
        except:
            pass
        return User(user['id'], user['username'], user['email'], user['password'], is_admin, status)
    return None
