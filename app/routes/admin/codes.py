"""
Rutas de administración de códigos.
Gestión de códigos de todos los usuarios.
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import get_db_connection

bp = Blueprint('admin_codes', __name__)


@bp.route('/admin_codes')
@login_required
def admin_codes():
    """Ver códigos de todos los usuarios"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    codes = conn.execute('''
        SELECT pc.*, u.username, u.email 
        FROM processing_codes pc
        JOIN users u ON pc.user_id = u.id
        ORDER BY pc.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_codes.html', username=current_user.username, codes=codes)


@bp.route('/admin_delete_code/<int:code_id>')
@login_required
def admin_delete_code(code_id):
    """Eliminar un código de cualquier usuario"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    code = conn.execute('SELECT * FROM processing_codes WHERE id = ?', (code_id,)).fetchone()
    
    if code:
        if code['image_path']:
            try:
                os.remove(code['image_path'])
            except OSError:
                pass
        
        conn.execute('DELETE FROM processing_codes WHERE id = ?', (code_id,))
        conn.commit()
        flash('Código eliminado exitosamente', 'success')
    else:
        flash('Código no encontrado', 'danger')
    
    conn.close()
    return redirect(url_for('admin_codes'))


@bp.route('/admin_view_code/<int:code_id>')
@login_required
def admin_view_code(code_id):
    """Ver un código específico"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    code = conn.execute('''
        SELECT pc.*, u.username, u.email 
        FROM processing_codes pc
        JOIN users u ON pc.user_id = u.id
        WHERE pc.id = ?
    ''', (code_id,)).fetchone()
    conn.close()
    
    if not code:
        flash('Código no encontrado', 'danger')
        return redirect(url_for('admin_codes'))
    
    return render_template('admin_view_code.html', username=current_user.username, code=code)
