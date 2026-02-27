"""
Funciones helper utilities.
Funciones auxiliares para la aplicación.
"""
import os
import uuid


def save_uploaded_file(file, upload_folder):
    """
    Guarda un archivo subido y retorna la ruta.
    
    Args:
        file: Archivo a guardar (FileStorage de Flask)
        upload_folder: Directorio donde guardar el archivo
        
    Returns:
        str: Ruta del archivo guardado
    """
    if file and file.filename != '':
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return unique_filename
    return None


def delete_file(file_path):
    """
    Elimina un archivo si existe.
    
    Args:
        file_path: Ruta del archivo a eliminar
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
