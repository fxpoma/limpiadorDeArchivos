"""
Limpiador de Archivos - Punto de entrada de la aplicación.
Este archivo sirve como punto de entrada backward compatible.
La aplicación principal está en app/__init__.py
"""
import os

# Importar la aplicación desde el paquete app
from app import create_app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Usar la configuración de config.py
    from config import Config
    port = Config.PORT
    debug = Config.DEBUG
    
    print(f"Iniciando servidor en puerto {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
