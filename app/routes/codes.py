"""
Rutas de gestión de códigos.
Maneja la creación, edición y eliminación de códigos de procesamiento.
"""
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import get_db_connection

bp = Blueprint('codes', __name__)


@bp.route('/manage_codes', methods=['GET', 'POST'])
@login_required
def manage_codes():
    """Gestión de códigos de procesamiento"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        code_name = request.form['code_name']
        code_description = request.form['code_description']
        code_content = request.form['code_content']
        code_image = request.files.get('code_image')
        
        image_path = None
        if code_image and code_image.filename != '':
            image_extension = os.path.splitext(code_image.filename)[1]
            image_filename = f"{uuid.uuid4().hex}{image_extension}"
            image_path = os.path.join(current_app.config['CODES_FOLDER'], image_filename)
            code_image.save(image_path)
        
        conn.execute('INSERT INTO processing_codes (user_id, name, description, code, image_path) VALUES (?, ?, ?, ?, ?)',
                     (current_user.id, code_name, code_description, code_content, image_path))
        conn.commit()
        flash('Código guardado exitosamente', 'success')
        return redirect(url_for('manage_codes'))
    
    codes = conn.execute('SELECT * FROM processing_codes WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('manage_codes.html', username=current_user.username, codes=codes)


@bp.route('/delete_code/<int:code_id>')
@login_required
def delete_code(code_id):
    """Eliminar un código"""
    conn = get_db_connection()
    code = conn.execute('SELECT * FROM processing_codes WHERE id = ? AND user_id = ?', (code_id, current_user.id)).fetchone()
    
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
        flash('Código no encontrado o no tienes permiso para eliminarlo', 'danger')
    
    conn.close()
    return redirect(url_for('manage_codes'))


@bp.route('/edit_code/<int:code_id>', methods=['GET', 'POST'])
@login_required
def edit_code(code_id):
    """Editar un código"""
    conn = get_db_connection()
    code = conn.execute('SELECT * FROM processing_codes WHERE id = ? AND user_id = ?', (code_id, current_user.id)).fetchone()
    
    if not code:
        conn.close()
        flash('Código no encontrado o no tienes permiso para editarlo', 'danger')
        return redirect(url_for('manage_codes'))
    
    if request.method == 'POST':
        code_name = request.form['code_name']
        code_description = request.form['code_description']
        code_content = request.form['code_content']
        code_image = request.files.get('code_image')
        
        image_path = code['image_path']
        if code_image and code_image.filename != '':
            # Eliminar imagen anterior si existe
            if code['image_path']:
                try:
                    os.remove(code['image_path'])
                except OSError:
                    pass
            
            image_extension = os.path.splitext(code_image.filename)[1]
            image_filename = f"{uuid.uuid4().hex}{image_extension}"
            image_path = os.path.join(current_app.config['CODES_FOLDER'], image_filename)
            code_image.save(image_path)
        
        conn.execute('''
            UPDATE processing_codes 
            SET name = ?, description = ?, code = ?, image_path = ?
            WHERE id = ?
        ''', (code_name, code_description, code_content, image_path, code_id))
        conn.commit()
        conn.close()
        
        flash('Código actualizado exitosamente', 'success')
        return redirect(url_for('manage_codes'))
    
    conn.close()
    return render_template('edit_code.html', username=current_user.username, code=code)
