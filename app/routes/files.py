"""
Rutas de procesamiento de archivos.
Maneja upload, process, download y cleanup.
"""
import os
import uuid
import subprocess
import tempfile
import shutil
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from app.models import get_db_connection
from app.services import update_user_stats, update_daily_stats, record_activity
from app.utils.validators import check_dangerous_code

bp = Blueprint('files', __name__)


@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Subir archivo"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se ha seleccionado ningun archivo'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No se ha seleccionado ningun archivo'})
    
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        conn = get_db_connection()
        codes = conn.execute('SELECT * FROM processing_codes WHERE user_id = ?', (current_user.id,)).fetchall()
        conn.close()
        
        codes_list = []
        for code in codes:
            code_info = {
                'id': code['id'],
                'name': code['name'],
                'description': code['description'],
                'image_path': code['image_path']
            }
            codes_list.append(code_info)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'file_path': unique_filename,
            'codes': codes_list
        })


@bp.route('/process', methods=['POST'])
@login_required
def process_file():
    """Procesar archivo con código"""
    data = request.get_json()
    file_path = data['file_path']
    code_id = data['code_id']
    
    conn = get_db_connection()
    code = conn.execute('SELECT * FROM processing_codes WHERE id = ? AND user_id = ?', (code_id, current_user.id)).fetchone()
    conn.close()
    
    if not code:
        return jsonify({'success': False, 'error': 'Codigo no encontrado'})
    
    is_dangerous, message = check_dangerous_code(code['code'])
    if is_dangerous:
        return jsonify({'success': False, 'error': f'Codigo bloqueado por seguridad: {message}'})
    
    input_file = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    
    # Listar archivos en uploads antes de ejecutar
    files_before = set(os.listdir(current_app.config['UPLOAD_FOLDER']))
    
    # Usar rutas absolutas para que el codigo pueda encontrar los archivos
    abs_input_file = os.path.abspath(input_file)
    abs_uploads = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code['code'])
            temp_code_path = f.name
        
        # Configurar entorno para UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # Lista de archivos en varios directorios antes de ejecutar
        app_root_dir = os.getcwd()
        temp_dir = tempfile.gettempdir()
        
        files_before_root = set(os.listdir(app_root_dir))
        files_before_uploads = set(os.listdir(current_app.config['UPLOAD_FOLDER']))
        files_before_temp = set(os.listdir(temp_dir))
        
        # Ejecutar el codigo Python en el directorio de uploads
        result = subprocess.run(
            ['python', '-X', 'utf8', temp_code_path, abs_input_file],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=abs_uploads,
            env=env
        )
        
        os.remove(temp_code_path)
        
        if result.returncode != 0:
            raise Exception(f"Error al ejecutar el codigo: {result.stderr}")
        
        # Buscar el archivo generado en diferentes ubicaciones
        output_filename = None
        search_dirs = [
            (current_app.config['UPLOAD_FOLDER'], 'uploads'),
            (app_root_dir, 'root'),
            (temp_dir, 'temp'),
        ]
        
        # Primero buscar cualquier archivo csv existente
        all_csv_files = []
        for search_dir, dir_name in search_dirs:
            try:
                current_files = os.listdir(search_dir)
                csv_files = [f for f in current_files if f.endswith('.csv')]
                if csv_files:
                    all_csv_files.extend([(dir_name, f) for f in csv_files])
                print(f"Debug - {dir_name} archivos: {current_files}")
            except Exception as e:
                print(f"Debug - Error en {dir_name}: {e}")
        
        print(f"Debug - Archivos CSV encontrados: {all_csv_files}")
        
        # Buscar el archivo basado en el nombre del stdout
        match = re.search(r'(\S+\.csv)', result.stdout)
        if match:
            expected_filename = match.group(1)
            print(f"Debug - Buscando archivo: {expected_filename}")
            
            for search_dir, dir_name in search_dirs:
                if os.path.exists(os.path.join(search_dir, expected_filename)):
                    output_filename = expected_filename
                    print(f"Debug - Encontrado en {dir_name}: {expected_filename}")
                    if dir_name != 'uploads':
                        src = os.path.join(search_dir, expected_filename)
                        dst = os.path.join(current_app.config['UPLOAD_FOLDER'], expected_filename)
                        shutil.move(src, dst)
                    break
        
        if not output_filename and all_csv_files:
            # Usar el primer archivo csv encontrado
            dir_name, output_filename = all_csv_files[0]
            print(f"Debug - Usando primer CSV encontrado: {dir_name}/{output_filename}")
            if dir_name != 'uploads':
                src = os.path.join(eval(dir_name + '_dir'), output_filename)
                dst = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
                shutil.move(src, dst)
        
        if not output_filename:
            raise Exception(f"No se detecto ningun archivo CSV. Archivos: {all_csv_files}. Stdout: {result.stdout[:300]}")
        
        # Registrar procesamiento de archivo exitoso
        try:
            update_user_stats(current_user.id, file_processed=True)
            update_daily_stats(file_processing=True)
            record_activity(current_user.id, 'file_processed', f'Archivo procesado: {file_path}', request.remote_addr, request.headers.get('User-Agent'))
        except Exception as e:
            print(f"Error al registrar stats de procesamiento: {e}")
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'filename': output_filename
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """Descargar archivo"""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        flash('Archivo no encontrado', 'danger')
        return redirect(url_for('index'))


@bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_files():
    """Limpiar archivos"""
    data = request.get_json()
    input_file = data['input_file']
    output_file = data.get('output_file')
    
    try:
        if input_file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], input_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if output_file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
