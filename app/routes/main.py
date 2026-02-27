"""
Rutas principales.
Maneja index, profile y cambio de contraseña.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt
from app.models import get_db_connection
from app.services import update_daily_stats
import os

bp = Blueprint('main', __name__)


@bp.route('/debug/db')
def debug_db():
    """Ruta de debug para verificar la base de datos"""
    from config import get_db_path
    db_path = get_db_path()
    conn = get_db_connection()
    
    # Contar usuarios
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    
    # Obtener usuarios
    users = conn.execute('SELECT id, username, email, is_admin, status FROM users').fetchall()
    conn.close()
    
    return jsonify({
        'db_path': db_path,
        'db_exists': os.path.exists(db_path),
        'user_count': user_count['count'],
        'users': [dict(u) for u in users]
    })


@bp.route('/')
def index():
    """Página principal"""
    # Si no hay usuarios, redirigir al registro
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    conn.close()
    
    # Registrar visita a página
    try:
        update_daily_stats(page_view=True)
    except Exception as e:
        print(f"Error al registrar visita: {e}")
    
    if user_count['count'] == 0:
        return redirect(url_for('auth.register'))
    
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return redirect(url_for('auth.login'))


@bp.route('/profile')
@login_required
def profile():
    """Página de perfil de usuario"""
    conn = get_db_connection()
    codes = conn.execute('SELECT * FROM processing_codes WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profile.html', username=current_user.username, codes=codes)


@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambio de contraseña"""
    bcrypt = Bcrypt()
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
        conn.close()
        
        if not bcrypt.check_password_hash(user['password'], current_password):
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'danger')
            return redirect(url_for('change_password'))
        
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, current_user.id))
        conn.commit()
        conn.close()
        
        flash('Contraseña cambiada exitosamente', 'success')
        return redirect(url_for('profile'))
    
    return render_template('change_password.html', username=current_user.username)
