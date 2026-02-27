"""
Rutas de estadísticas de administración.
Dashboard de estadísticas del sistema.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import get_db_connection

bp = Blueprint('admin_stats', __name__)


@bp.route('/admin_stats')
@login_required
def admin_stats():
    """Dashboard de estadísticas del sistema"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Estadísticas generales
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    total_codes = conn.execute('SELECT COUNT(*) as count FROM processing_codes').fetchone()
    approved_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'approved'").fetchone()
    pending_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'pending'").fetchone()
    
    # Estadísticas de usuarios
    user_stats = conn.execute('''
        SELECT 
            SUM(login_count) as total_logins,
            SUM(file_processed_count) as total_files_processed,
            COUNT(*) as active_users
        FROM user_stats
    ''').fetchone()
    
    # Estadísticas de los últimos 7 días
    last_7_days = conn.execute('''
        SELECT 
            stat_date,
            page_views,
            logins,
            file_processing,
            new_users
        FROM daily_stats 
        WHERE stat_date >= date('now', '-7 days')
        ORDER BY stat_date DESC
    ''').fetchall()
    
    # Top usuarios más activos
    top_users = conn.execute('''
        SELECT 
            u.username,
            us.login_count,
            us.file_processed_count,
            us.last_login,
            us.last_activity
        FROM user_stats us
        JOIN users u ON us.user_id = u.id
        ORDER BY (us.login_count + us.file_processed_count) DESC
        LIMIT 10
    ''').fetchall()
    
    # Actividad reciente
    recent_activity = conn.execute('''
        SELECT 
            al.action,
            al.details,
            al.ip_address,
            al.created_at,
            u.username
        FROM activity_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 20
    ''').fetchall()
    
    # Estadísticas mensuales
    monthly_stats = conn.execute('''
        SELECT 
            strftime('%Y-%m', stat_date) as month,
            SUM(page_views) as total_views,
            SUM(logins) as total_logins,
            SUM(file_processing) as total_processing,
            SUM(new_users) as total_new_users
        FROM daily_stats
        WHERE stat_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', stat_date)
        ORDER BY month DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template(
        'admin_stats.html',
        username=current_user.username,
        total_users=total_users['count'],
        total_codes=total_codes['count'],
        approved_users=approved_users['count'],
        pending_users=pending_users['count'],
        user_stats=user_stats,
        last_7_days=last_7_days,
        top_users=top_users,
        recent_activity=recent_activity,
        monthly_stats=monthly_stats
    )
