"""
Rutas de autenticación.
Maneja login, register y logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from app.models import get_db_connection
from app.services import record_activity, update_user_stats, update_daily_stats
from app.models.user import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta de inicio de sesión"""
    # Si no hay usuarios, redirigir al registro
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    conn.close()
    
    if user_count['count'] == 0:
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        login_input = request.form['email']  # Puede ser email o username
        password = request.form['password']
        
        conn = get_db_connection()
        # Buscar por email o username
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', 
            (login_input, login_input)
        ).fetchone()
        conn.close()
        
        bcrypt = Bcrypt()
        if user and bcrypt.check_password_hash(user['password'], password):
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
            
            # Verificar si el usuario está aprobado o es admin
            if status != 'approved' and is_admin != 1:
                flash('Tu cuenta está pendiente de aprobación. Por favor, espera a que un administrador apruebe tu solicitud.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_obj = User(user['id'], user['username'], user['email'], user['password'], is_admin, status)
            login_user(user_obj)
            
            # Registrar estadísticas de login
            try:
                update_user_stats(user['id'], login=True)
                update_daily_stats(login=True)
                record_activity(user['id'], 'login', 'Usuario inició sesión', request.remote_addr, request.headers.get('User-Agent'))
            except Exception as e:
                print(f"Error al registrar stats de login: {e}")
            
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Credenciales inválidas', 'danger')
    
    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta de registro de usuario"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))
        
        bcrypt = Bcrypt()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        conn = get_db_connection()
        
        # Verificar si es el primer usuario (se convertirá en admin)
        user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
        is_first_user = user_count['count'] == 0
        
        # Determinar status: approved si es el primer usuario, pending si no
        user_status = 'approved' if is_first_user else 'pending'
        user_is_admin = 1 if is_first_user else 0
        
        try:
            cursor = conn.execute('INSERT INTO users (username, email, password, status, is_admin) VALUES (?, ?, ?, ?, ?)',
                         (username, email, hashed_password, user_status, user_is_admin))
            conn.commit()
            new_user_id = cursor.lastrowid
            conn.close()
            
            # Registrar nuevo usuario en estadísticas
            try:
                update_daily_stats(new_user=True)
                # Usar request solo si está disponible
                ip_addr = getattr(request, 'remote_addr', None)
                user_agnt = getattr(request, 'headers', lambda: {}).get('User-Agent', None) if request else None
                record_activity(new_user_id, 'register', f'Nuevo usuario registrado: {username}', ip_addr, user_agnt)
            except Exception as e:
                print(f"Error al registrar stats de nuevo usuario: {e}")
            
            if is_first_user:
                flash('Registro exitoso! Has sido registrado como administrador.', 'success')
            else:
                flash('Registro exitoso! Tu solicitud está pendiente de aprobación. Un administrador revisará tu cuenta pronto.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('El nombre de usuario o email ya existe', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')


@bp.route('/logout')
@login_required
def logout():
    """Ruta de cierre de sesión"""
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))
