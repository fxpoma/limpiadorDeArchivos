from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import os
import uuid
import subprocess
import tempfile
import shutil
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-aqui')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['CODES_FOLDER'] = os.getenv('CODES_FOLDER', 'static/codes')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PORT'] = int(os.getenv('FLASK_RUN_PORT', 5000))

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CODES_FOLDER'], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    
    # Crear tabla de usuarios si no existe
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar columna is_admin si no existe (para bases de datos existentes)
    try:
        conn.execute('SELECT is_admin FROM users LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
    
    # Agregar columna status si no existe (para bases de datos existentes)
    try:
        conn.execute('SELECT status FROM users LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'pending'")
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS processing_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            code TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS python_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT UNIQUE NOT NULL,
            installed_by INTEGER,
            installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear admin si no existe (comentado para que el primer usuario sea admin)
    # admin = conn.execute('SELECT * FROM users WHERE is_admin = 1').fetchone()
    # if not admin:
    #     admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
    #     try:
    #         conn.execute('INSERT INTO users (username, email, password, is_admin, status) VALUES (?, ?, ?, ?, ?)',
    #                      ('admin', 'admin@localhost', admin_password, 1, 'approved'))
    #     except sqlite3.IntegrityError:
    #         pass
    
    conn.commit()
    conn.close()


class User(UserMixin):
    def __init__(self, id, username, email, password, is_admin=0, status='pending'):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.status = status


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
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
        return User(user['id'], user['username'], user['email'], user['password'], is_admin, status)
    return None


@app.route('/')
def index():
    # Si no hay usuarios, redirigir al registro
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    conn.close()
    
    if user_count['count'] == 0:
        return redirect(url_for('register'))
    
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si no hay usuarios, redirigir al registro
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    conn.close()
    
    if user_count['count'] == 0:
        return redirect(url_for('register'))
    
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
                return redirect(url_for('login'))
            
            user_obj = User(user['id'], user['username'], user['email'], user['password'], is_admin, status)
            login_user(user_obj)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales inválidas', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        conn = get_db_connection()
        
        # Verificar si es el primer usuario (se convertirá en admin)
        user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
        is_first_user = user_count['count'] == 0
        
        # Determinar status: approved si es el primer usuario, pending si no
        user_status = 'approved' if is_first_user else 'pending'
        user_is_admin = 1 if is_first_user else 0
        
        try:
            conn.execute('INSERT INTO users (username, email, password, status, is_admin) VALUES (?, ?, ?, ?, ?)',
                         (username, email, hashed_password, user_status, user_is_admin))
            conn.commit()
            conn.close()
            
            if is_first_user:
                flash('Registro exitoso! Has sido registrado como administrador.', 'success')
            else:
                flash('Registro exitoso! Tu solicitud está pendiente de aprobación. Un administrador revisará tu cuenta pronto.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario o email ya existe', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    codes = conn.execute('SELECT * FROM processing_codes WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profile.html', username=current_user.username, codes=codes)


@app.route('/manage_codes', methods=['GET', 'POST'])
@login_required
def manage_codes():
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
            image_path = os.path.join(app.config['CODES_FOLDER'], image_filename)
            code_image.save(image_path)
        
        conn.execute('INSERT INTO processing_codes (user_id, name, description, code, image_path) VALUES (?, ?, ?, ?, ?)',
                     (current_user.id, code_name, code_description, code_content, image_path))
        conn.commit()
        flash('Código guardado exitosamente', 'success')
        return redirect(url_for('manage_codes'))
    
    codes = conn.execute('SELECT * FROM processing_codes WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('manage_codes.html', username=current_user.username, codes=codes)


@app.route('/delete_code/<int:code_id>')
@login_required
def delete_code(code_id):
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


@app.route('/edit_code/<int:code_id>', methods=['GET', 'POST'])
@login_required
def edit_code(code_id):
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
            image_path = os.path.join(app.config['CODES_FOLDER'], image_filename)
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


def check_dangerous_code(code):
    dangerous_patterns = [
        r'pip\s+install',
        r'pip3\s+install',
        r'subprocess\.(run|call|Popen|check_output)',
        r'os\.system',
        r'os\.popen',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
        r'import\s+subprocess',
        r'import\s+os\s*;\s*system',
        r'pip\.',
        r'conda\s+install',
        r'!\s*pip',
        r'!\s*conda',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return True, f"Codigo potencialmente peligroso detectado: {pattern}"
    
    return False, "Codigo seguro"


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se ha seleccionado ningun archivo'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No se ha seleccionado ningun archivo'})
    
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
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


@app.route('/process', methods=['POST'])
@login_required
def process_file():
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
    
    input_file = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
    
    # Listar archivos en uploads antes de ejecutar
    files_before = set(os.listdir(app.config['UPLOAD_FOLDER']))
    
    # Usar rutas absolutas para que el codigo pueda encontrar los archivos
    abs_input_file = os.path.abspath(input_file)
    abs_uploads = os.path.abspath(app.config['UPLOAD_FOLDER'])
    
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
        files_before_uploads = set(os.listdir(app.config['UPLOAD_FOLDER']))
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
            (app.config['UPLOAD_FOLDER'], 'uploads'),
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
        # El stdout dice: movimientos_actual_budget_20260123_20260220.csv
        import re
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
                        dst = os.path.join(app.config['UPLOAD_FOLDER'], expected_filename)
                        shutil.move(src, dst)
                    break
        
        if not output_filename and all_csv_files:
            # Usar el primer archivo csv encontrado
            dir_name, output_filename = all_csv_files[0]
            print(f"Debug - Usando primer CSV encontrado: {dir_name}/{output_filename}")
            if dir_name != 'uploads':
                src = os.path.join(eval(dir_name + '_dir'), output_filename)
                dst = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                shutil.move(src, dst)
        
        if not output_filename:
            raise Exception(f"No se detecto ningun archivo CSV. Archivos: {all_csv_files}. Stdout: {result.stdout[:300]}")
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'filename': output_filename
        })
        
        final_filename = output_filename
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'filename': final_filename
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download/<filename>')
@login_required
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        flash('Archivo no encontrado', 'danger')
        return redirect(url_for('index'))


@app.route('/cleanup', methods=['POST'])
@login_required
def cleanup_files():
    data = request.get_json()
    input_file = data['input_file']
    output_file = data.get('output_file')
    
    try:
        if input_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], input_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if output_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/manage_modules')
@login_required
def manage_modules():
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    modules = conn.execute('SELECT * FROM python_modules ORDER BY installed_at DESC').fetchall()
    conn.close()
    return render_template('manage_modules.html', username=current_user.username, modules=modules)


@app.route('/install_module', methods=['POST'])
@login_required
def install_module():
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


@app.route('/uninstall_module/<module_name>')
@login_required
def uninstall_module(module_name):
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


@app.route('/get_installed_modules')
@login_required
def get_installed_modules():
    conn = get_db_connection()
    modules = conn.execute('SELECT module_name FROM python_modules').fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'modules': [m['module_name'] for m in modules]
    })


# Ruta para hacer a un usuario administrador (solo para el admin actual)
@app.route('/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Usuario convertido en administrador exitosamente', 'success')
    return redirect(url_for('admin_users'))


# Ruta para quitar admin a un usuario (solo para el admin actual)
@app.route('/remove_admin/<int:user_id>')
@login_required
def remove_admin(user_id):
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


# Ruta para eliminar un usuario (solo admin)
@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
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


# Ruta para aprobar un usuario (solo admin)
@app.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
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


# Ruta para rechazar/eliminar una solicitud de registro (solo admin)
@app.route('/reject_user/<int:user_id>')
@login_required
def reject_user(user_id):
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


# Ruta para editar un usuario (solo admin)
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
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


# Ruta para ver y administrar usuarios (solo admin)
@app.route('/admin_users')
@login_required
def admin_users():
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


# Ruta para ver códigos de todos los usuarios (solo admin)
@app.route('/admin_codes')
@login_required
def admin_codes():
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


# Ruta para eliminar un código de cualquier usuario (solo admin)
@app.route('/admin_delete_code/<int:code_id>')
@login_required
def admin_delete_code(code_id):
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


# Ruta para ver un código específico (solo admin)
@app.route('/admin_view_code/<int:code_id>')
@login_required
def admin_view_code(code_id):
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


# Ruta para cambiar contraseña
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
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


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
