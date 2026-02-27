"""
Rutas de administración de módulos.
Gestión de módulos Python instalados.
"""
import subprocess
import sys
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
from app.models import get_db_connection

bp = Blueprint('admin_modules', __name__)


@bp.route('/manage_modules')
@login_required
def manage_modules():
    """Gestión de módulos Python"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    modules = conn.execute('SELECT * FROM python_modules ORDER BY installed_at DESC').fetchall()
    conn.close()
    return render_template('manage_modules.html', username=current_user.username, modules=modules)


@bp.route('/install_module', methods=['POST'])
@login_required
def install_module():
    """Instalar un módulo"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No tienes permisos de administrador'})
    
    module_name = request.form.get('module_name', '').strip()
    
    if not module_name:
        return jsonify({'success': False, 'error': 'Debe especificar el nombre del modulo'})
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', module_name):
        return jsonify({'success': False, 'error': 'Nombre de modulo invalido'})
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', module_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': f'Error al instalar: {result.stderr}'})
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO python_modules (module_name, installed_by) VALUES (?, ?)',
                         (module_name, current_user.id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'El modulo ya esta instalado'})
        
        conn.close()
        return jsonify({'success': True, 'message': f'Modulo {module_name} instalado correctamente'})
    
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Tiempo de espera agotado al instalar el modulo'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/uninstall_module/<module_name>')
@login_required
def uninstall_module(module_name):
    """Desinstalar un módulo"""
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', '-y', module_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            flash(f'Error al desinstalar: {result.stderr}', 'danger')
            return redirect(url_for('manage_modules'))
        
        conn = get_db_connection()
        conn.execute('DELETE FROM python_modules WHERE module_name = ?', (module_name,))
        conn.commit()
        conn.close()
        
        flash(f'Modulo {module_name} desinstalado correctamente', 'success')
    except Exception as e:
        flash(f'Error al desinstalar: {str(e)}', 'danger')
    
    return redirect(url_for('manage_modules'))


@bp.route('/get_installed_modules')
@login_required
def get_installed_modules():
    """Obtener lista de módulos instalados"""
    conn = get_db_connection()
    modules = conn.execute('SELECT module_name FROM python_modules').fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'modules': [m['module_name'] for m in modules]
    })
