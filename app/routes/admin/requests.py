"""
Rutas de estadísticas de requests.
Dashboard de estadísticas de consultas del sistema.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import get_db_connection
from app.services import block_ip

bp = Blueprint('admin_requests', __name__)


@bp.route('/admin_request_stats')
@login_required
def admin_request_stats():
    """Dashboard de estadísticas de consultas"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Obtener parámetros de filtro
    page = request.args.get('page', 1, type=int)
    per_page = 50
    filter_path = request.args.get('path', '')
    filter_method = request.args.get('method', '')
    filter_status = request.args.get('status', '')
    
    # Construir consulta base
    base_query = '''
        SELECT 
            rl.id,
            rl.ip_address,
            rl.method,
            rl.path,
            rl.status_code,
            rl.response_time,
            rl.user_agent,
            rl.created_at,
            u.username
        FROM request_logs rl
        LEFT JOIN users u ON rl.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if filter_path:
        base_query += ' AND rl.path LIKE ?'
        params.append(f'%{filter_path}%')
    if filter_method:
        base_query += ' AND rl.method = ?'
        params.append(filter_method)
    if filter_status:
        base_query += ' AND rl.status_code = ?'
        params.append(filter_status)
    
    # Contar total de registros
    count_query = 'SELECT COUNT(*) as total FROM (' + base_query + ') as subquery'
    total_result = conn.execute(count_query, params).fetchone()
    total_count = total_result['total'] if total_result else 0
    
    # Obtener paginación
    paginated_query = base_query + ' ORDER BY rl.created_at DESC LIMIT ? OFFSET ?'
    params_paged = params.copy()
    params_paged.extend([per_page, (page - 1) * per_page])
    
    request_logs = conn.execute(paginated_query, params_paged).fetchall()
    
    # Estadísticas de rutas más visitadas
    top_routes = conn.execute('''
        SELECT 
            route,
            method,
            hit_count,
            avg_response_time,
            last_accessed
        FROM route_stats
        ORDER BY hit_count DESC
        LIMIT 20
    ''').fetchall()
    
    # Estadísticas de IPs
    top_ips = conn.execute('''
        SELECT 
            ip_address,
            COUNT(*) as request_count,
            MAX(created_at) as last_request
        FROM request_logs
        GROUP BY ip_address
        ORDER BY request_count DESC
        LIMIT 20
    ''').fetchall()
    
    # Resumen de códigos de estado
    status_summary = conn.execute('''
        SELECT 
            status_code,
            COUNT(*) as count
        FROM request_logs
        WHERE status_code IS NOT NULL
        GROUP BY status_code
        ORDER BY count DESC
    ''').fetchall()
    
    # Promedio de tiempo de respuesta
    avg_response = conn.execute('''
        SELECT AVG(response_time) as avg_time, MAX(response_time) as max_time, MIN(response_time) as min_time
        FROM request_logs
        WHERE response_time IS NOT NULL
    ''').fetchone()
    
    # Total de requests
    total_requests = conn.execute('SELECT COUNT(*) as count FROM request_logs').fetchone()
    
    conn.close()
    
    return render_template(
        'admin_request_stats.html',
        username=current_user.username,
        request_logs=request_logs,
        top_routes=top_routes,
        top_ips=top_ips,
        status_summary=status_summary,
        avg_response=avg_response,
        total_requests=total_requests['count'],
        page=page,
        per_page=per_page,
        total_count=total_count,
        filter_path=filter_path,
        filter_method=filter_method,
        filter_status=filter_status
    )


@bp.route('/admin_block_ip', methods=['POST'])
@login_required
def admin_block_ip():
    """Bloquea una IP"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permisos de administrador'})
    
    data = request.get_json()
    ip_address = data.get('ip_address', '')
    reason = data.get('reason', '')
    permanent = data.get('permanent', False)
    duration = data.get('duration', 24)
    
    if not ip_address:
        return jsonify({'success': False, 'error': 'Debe especificar una IP'})
    
    success = block_ip(ip_address, reason, permanent, duration)
    
    if success:
        return jsonify({'success': True, 'message': f'IP {ip_address} bloqueada correctamente'})
    else:
        return jsonify({'success': False, 'error': 'Error al bloquear la IP'})


@bp.route('/admin_blocked_ips')
@login_required
def admin_blocked_ips():
    """Ver lista de IPs bloqueadas"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    blocked_ips = conn.execute('''
        SELECT * FROM blocked_ips 
        WHERE is_permanent = 1 OR expires_at > ?
        ORDER BY blocked_at DESC
    ''', (now,)).fetchall()
    conn.close()
    
    return render_template(
        'admin_blocked_ips.html',
        username=current_user.username,
        blocked_ips=blocked_ips
    )


@bp.route('/admin_unblock_ip/<ip_address>')
@login_required
def admin_unblock_ip(ip_address):
    """Desbloquea una IP"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    from app.services.security_service import unblock_ip
    unblock_ip(ip_address)
    
    flash(f'IP {ip_address} desbloqueada correctamente', 'success')
    return redirect(url_for('admin_blocked_ips'))
