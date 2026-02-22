#!/bin/bash

# Inicializar base de datos si no existe
if [ ! -f "database.db" ]; then
    echo "Creando base de datos..."
    python -c "import sqlite3; conn = sqlite3.connect('database.db'); conn.close()"
fi

# Iniciar aplicación Flask
echo "Iniciando aplicación Flask..."
exec python app.py
