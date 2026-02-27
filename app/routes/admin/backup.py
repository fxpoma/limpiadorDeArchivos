"""
Rutas de administración - Backup de base de datos.
Permite hacer backup y restaurar la base de datos.
"""
from flask import Blueprint, send_file, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import get_db_connection
import os
import shutil
from datetime import datetime

bp = Blueprint('backup', __name__)


@bp.route('/admin/backup', methods=['GET', 'POST'])
@login_required
def create_backup():
    """Crear un backup de la base de datos"""
    # Verificar que es admin
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            from config import get_db_path
            db_path = get_db_path()
            
            # Crear directorio de backups si no existe
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generar nombre de archivo con fecha
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copiar la base de datos
            shutil.copy2(db_path, backup_path)
            
            # Limpiar backups antiguos (mantener solo los últimos 10)
            backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('backup_')])
            while len(backups) > 10:
                old_backup = backups.pop(0)
                os.remove(os.path.join(backup_dir, old_backup))
            
            flash(f'Backup creado exitosamente: {backup_filename}', 'success')
        except Exception as e:
            flash(f'Error al crear backup: {str(e)}', 'danger')
    
    # Mostrar lista de backups
    from config import get_db_path
    db_path = get_db_path()
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    
    backups = []
    if os.path.exists(backup_dir):
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.startswith('backup_'):
                file_path = os.path.join(backup_dir, f)
                backups.append({
                    'name': f,
                    'size': os.path.getsize(file_path),
                    'date': datetime.fromtimestamp(os.path.getmtime(file_path))
                })
    
    return jsonify({
        'success': True,
        'backups': [{'name': b['name'], 'size': b['size'], 'date': b['date'].isoformat()} for b in backups]
    })


@bp.route('/admin/backup/download/<filename>')
@login_required
def download_backup(filename):
    """Descargar un archivo de backup"""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    from config import get_db_path
    db_path = get_db_path()
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    backup_file = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_file):
        flash('Archivo de backup no encontrado', 'danger')
        return redirect(url_for('main.index'))
    
    return send_file(backup_file, as_attachment=True, download_name=filename)


@bp.route('/admin/backup/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    """Restaurar un backup"""
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        from config import get_db_path
        db_path = get_db_path()
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        backup_file = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_file):
            return jsonify({'success': False, 'error': 'Archivo de backup no encontrado'})
        
        # Crear backup del estado actual antes de restaurar
        current_backup = os.path.join(backup_dir, f'pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, current_backup)
        
        # Restaurar el backup
        shutil.copy2(backup_file, db_path)
        
        return jsonify({'success': True, 'message': f'Backup restaurado desde {filename}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
