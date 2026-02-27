"""
Servicio de seguridad.
Funciones para bloquear y verificar IPs.
"""
from datetime import datetime
from app.models.database import get_db_connection


def is_ip_blocked(ip_address):
    """
    Verifica si una IP está bloqueada.
    
    Args:
        ip_address: IP a verificar
        
    Returns:
        bool: True si la IP está bloqueada, False en caso contrario
    """
    try:
        conn = get_db_connection()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        blocked = conn.execute(
            'SELECT * FROM blocked_ips WHERE ip_address = ? AND (is_permanent = 1 OR expires_at > ?)',
            (ip_address, now)
        ).fetchone()
        conn.close()
        return blocked is not None
    except Exception as e:
        print(f"Error al verificar IP bloqueada: {e}")
        return False


def block_ip(ip_address, reason='', permanent=False, duration_hours=24):
    """
    Bloquea una IP.
    
    Args:
        ip_address: IP a bloquear
        reason: Razón del bloqueo
        permanent: Si es True, el bloqueo es permanente
        duration_hours: Duración del bloqueo en horas (solo si permanent es False)
        
    Returns:
        bool: True si el bloqueo fue exitoso, False en caso contrario
    """
    try:
        conn = get_db_connection()
        expires_at = None if permanent else datetime.now().timestamp() + (duration_hours * 3600)
        expires_at_str = datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S') if expires_at else None
        
        conn.execute(
            'INSERT OR REPLACE INTO blocked_ips (ip_address, reason, expires_at, is_permanent) VALUES (?, ?, ?, ?)',
            (ip_address, reason, expires_at_str, 1 if permanent else 0)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al bloquear IP: {e}")
        return False


def unblock_ip(ip_address):
    """
    Desbloquea una IP.
    
    Args:
        ip_address: IP a desbloquear
        
    Returns:
        bool: True si el desbloqueo fue exitoso, False en caso contrario
    """
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip_address,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al desbloquear IP: {e}")
        return False


def get_blocked_ips():
    """
    Obtiene la lista de IPs bloqueadas.
    
    Returns:
        list: Lista de IPs bloqueadas
    """
    try:
        conn = get_db_connection()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        blocked_ips = conn.execute('''
            SELECT * FROM blocked_ips 
            WHERE is_permanent = 1 OR expires_at > ?
            ORDER BY blocked_at DESC
        ''', (now,)).fetchall()
        conn.close()
        return blocked_ips
    except Exception as e:
        print(f"Error al obtener IPs bloqueadas: {e}")
        return []
