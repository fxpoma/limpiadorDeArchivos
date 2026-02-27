"""
Rutas de API de estadísticas.
API JSON para obtener estadísticas.
"""
from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import get_db_connection

bp = Blueprint('api_stats', __name__, url_prefix='/api')


@bp.route('/stats/summary')
@login_required
def api_stats_summary():
    """API para obtener resumen de estadísticas en JSON"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permisos de administrador'})
    
    conn = get_db_connection()
    
    # Resumen general
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    total_codes = conn.execute('SELECT COUNT(*) as count FROM processing_codes').fetchone()
    
    # Stats de usuarios
    user_stats = conn.execute('''
        SELECT 
            SUM(login_count) as total_logins,
            SUM(file_processed_count) as total_files
        FROM user_stats
    ''').fetchone()
    
    # Stats de hoy
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = conn.execute('SELECT * FROM daily_stats WHERE stat_date = ?', (today,)).fetchone()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_users': total_users['count'],
            'total_codes': total_codes['count'],
            'total_logins': user_stats['total_logins'] or 0,
            'total_files_processed': user_stats['total_files'] or 0,
            'today': {
                'page_views': today_stats['page_views'] if today_stats else 0,
                'logins': today_stats['logins'] if today_stats else 0,
                'file_processing': today_stats['file_processing'] if today_stats else 0
            }
        }
    })


@bp.route('/request_stats')
@login_required
def api_request_stats():
    """API para obtener estadísticas de requests en JSON"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permisos de administrador'})
    
    conn = get_db_connection()
    
    # Requests por hora hoy
    hourly_today = conn.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as count
        FROM request_logs
        WHERE date(created_at) = date('now')
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()
    
    # Requests por ruta
    requests_by_route = conn.execute('''
        SELECT 
            path,
            method,
            COUNT(*) as count,
            AVG(response_time) as avg_time
        FROM request_logs
        GROUP BY path, method
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'hourly_today': [{'hour': h['hour'], 'count': h['count']} for h in hourly_today],
            'requests_by_route': [{
                'path': r['path'],
                'method': r['method'],
                'count': r['count'],
                'avg_time': round(r['avg_time'], 3) if r['avg_time'] else 0
            } for r in requests_by_route]
        }
    })
