"""
Rutas de administración de usuarios.
Gestión de usuarios (aprobar, eliminar, editar, hacer admin).
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt
import sqlite3
from app.models import get_db_connection

bp = Blueprint('admin_users', __name__)


@bp.route('/admin_users')
@login_required
def admin_users():
    """Ver y administrar usuarios"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    # Obtener usuarios pendientes (solicitudes de registro)
    pending_users = conn.execute("SELECT * FROM users WHERE status = 'pending' ORDER BY created_at DESC").fetchall()
    # Obtener usuarios aprobados
    approved_users = conn.execute("SELECT * FROM users WHERE status = 'approved' ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('admin_users.html', username=current_user.username, pending_users=pending_users, approved_users=approved_users)


@bp.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    """Aprobar un usuario"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
    conn.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    flash(f'Usuario {user["username"]} aprobado exitosamente. Ahora puede iniciar sesión.', 'success')
    return redirect(url_for('admin_users'))


@bp.route('/reject_user/<int:user_id>')
@login_required
def reject_user(user_id):
    """Rechazar/eliminar una solicitud de registro"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    # No permitirse eliminar a uno mismo
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
    # Eliminar códigos del usuario si existen
    codes = conn.execute('SELECT image_path FROM processing_codes WHERE user_id = ?', (user_id,)).fetchall()
    for code in codes:
        if code['image_path']:
            try:
                os.remove(code['image_path'])
            except OSError:
                pass
    
    conn.execute('DELETE FROM processing_codes WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Solicitud de registro rechazada y eliminada', 'success')
    return redirect(url_for('admin_users'))


@bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    """Eliminar un usuario"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    # No permitirse eliminar a uno mismo
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    
    # Eliminar códigos del usuario
    codes = conn.execute('SELECT image_path FROM processing_codes WHERE user_id = ?', (user_id,)).fetchall()
    for code in codes:
        if code['image_path']:
            try:
                os.remove(code['image_path'])
            except OSError:
                pass
    
    conn.execute('DELETE FROM processing_codes WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('admin_users'))


@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Editar un usuario"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
    bcrypt = Bcrypt()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_password = request.form.get('new_password', '').strip()
        is_admin = 1 if request.form.get('is_admin') else 0
        
        try:
            if new_password:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                conn.execute('''
                    UPDATE users SET username = ?, email = ?, password = ?, is_admin = ?
                    WHERE id = ?
                ''', (username, email, hashed_password, is_admin, user_id))
            else:
                conn.execute('''
                    UPDATE users SET username = ?, email = ?, is_admin = ?
                    WHERE id = ?
                ''', (username, email, is_admin, user_id))
            
            conn.commit()
            flash('Usuario actualizado exitosamente', 'success')
            conn.close()
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario o email ya existe', 'danger')
    
    conn.close()
    return render_template('edit_user.html', username=current_user.username, user=user)


@bp.route('/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    """Hacer a un usuario administrador"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Usuario convertido en administrador exitosamente', 'success')
    return redirect(url_for('admin_users'))


@bp.route('/remove_admin/<int:user_id>')
@login_required
def remove_admin(user_id):
    """Quitar admin a un usuario"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    # No permitir quitarse admin a uno mismo
    if user_id == current_user.id:
        flash('No puedes quitarte el admin a ti mismo', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Admin removido exitosamente', 'success')
    return redirect(url_for('admin_users'))
