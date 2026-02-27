"""
Servicio de estadísticas.
Funciones para registrar y actualizar estadísticas del sistema.
"""
from datetime import datetime
from app.models.database import get_db_connection


def record_activity(user_id, action, details=None, ip_address=None, user_agent=None):
    """
    Registra una actividad en los logs.
    
    Args:
        user_id: ID del usuario que realiza la acción
        action: Nombre de la acción
        details: Detalles adicionales de la acción
        ip_address: IP del usuario
        user_agent: User-Agent del navegador
    """
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, details, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al registrar actividad: {e}")


def update_user_stats(user_id, login=False, file_processed=False):
    """
    Actualiza las estadísticas de un usuario.
    
    Args:
        user_id: ID del usuario
        login: Si es True, incrementa el contador de logins
        file_processed: Si es True, incrementa el contador de archivos procesados
    """
    try:
        conn = get_db_connection()
        stats = conn.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,)).fetchone()
        
        if stats:
            # Actualizar stats existentes
            if login:
                conn.execute(
                    'UPDATE user_stats SET login_count = login_count + 1, last_login = CURRENT_TIMESTAMP, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (user_id,)
                )
            elif file_processed:
                conn.execute(
                    'UPDATE user_stats SET file_processed_count = file_processed_count + 1, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (user_id,)
                )
        else:
            # Crear stats nuevos
            login_count = 1 if login else 0
            file_count = 1 if file_processed else 0
            conn.execute(
                'INSERT INTO user_stats (user_id, login_count, file_processed_count, last_login, last_activity) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                (user_id, login_count, file_count)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al actualizar stats de usuario: {e}")


def update_daily_stats(page_view=False, login=False, file_processing=False, new_user=False):
    """
    Actualiza las estadísticas diarias del sistema.
    
    Args:
        page_view: Si es True, incrementa el contador de vistas de página
        login: Si es True, incrementa el contador de logins
        file_processing: Si es True, incrementa el contador de procesamiento de archivos
        new_user: Si es True, incrementa el contador de nuevos usuarios
    """
    try:
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        
        stats = conn.execute('SELECT * FROM daily_stats WHERE stat_date = ?', (today,)).fetchone()
        
        if stats:
            # Actualizar stats existentes
            if page_view:
                conn.execute('UPDATE daily_stats SET page_views = page_views + 1 WHERE stat_date = ?', (today,))
            if login:
                conn.execute('UPDATE daily_stats SET logins = logins + 1 WHERE stat_date = ?', (today,))
            if file_processing:
                conn.execute('UPDATE daily_stats SET file_processing = file_processing + 1 WHERE stat_date = ?', (today,))
            if new_user:
                conn.execute('UPDATE daily_stats SET new_users = new_users + 1 WHERE stat_date = ?', (today,))
        else:
            # Crear stats nuevos
            page_views = 1 if page_view else 0
            logins = 1 if login else 0
            file_processing_count = 1 if file_processing else 0
            new_users_count = 1 if new_user else 0
            conn.execute(
                'INSERT INTO daily_stats (stat_date, page_views, logins, file_processing, new_users) VALUES (?, ?, ?, ?, ?)',
                (today, page_views, logins, file_processing_count, new_users_count)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al actualizar stats diarios: {e}")


def record_request(user_id=None, ip_address=None, method=None, path=None, status_code=None, response_time=None, user_agent=None, referer=None):
    """
    Registra una consulta/request en los logs.
    
    Args:
        user_id: ID del usuario (si está autenticado)
        ip_address: IP del cliente
        method: Método HTTP
        path: Ruta solicitada
        status_code: Código de estado de la respuesta
        response_time: Tiempo de respuesta en segundos
        user_agent: User-Agent del navegador
        referer: Referer de la petición
    """
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO request_logs (user_id, ip_address, method, path, status_code, response_time, user_agent, referer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, ip_address, method, path, status_code, response_time, user_agent, referer)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al registrar request: {e}")


def update_route_stats(route, method, response_time, ip_address):
    """
    Actualiza las estadísticas de una ruta específica.
    
    Args:
        route: Ruta de la URL
        method: Método HTTP
        response_time: Tiempo de respuesta
        ip_address: IP del cliente
    """
    try:
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Buscar si ya existe el registro para esta ruta hoy
        stats = conn.execute(
            'SELECT * FROM route_stats WHERE route = ? AND method = ? AND date(last_accessed) = ?',
            (route, method, today)
        ).fetchone()
        
        if stats:
            # Actualizar stats existentes
            conn.execute(
                'UPDATE route_stats SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE route = ? AND method = ?',
                (route, method)
            )
            # Actualizar promedio de tiempo de respuesta
            new_avg = ((stats['avg_response_time'] * stats['hit_count']) + response_time) / (stats['hit_count'] + 1)
            conn.execute(
                'UPDATE route_stats SET avg_response_time = ? WHERE route = ? AND method = ?',
                (new_avg, route, method)
            )
        else:
            # Crear stats nuevos
            conn.execute(
                'INSERT INTO route_stats (route, method, hit_count, avg_response_time, last_accessed) VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)',
                (route, method, response_time)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al actualizar route stats: {e}")
