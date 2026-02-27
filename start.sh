#!/bin/bash

# =============================================================================
# Script de inicio para Limpiador de Archivos
# 
# Funcionalidades:
# - Detecta automáticamente el entorno (Docker/local)
# - Valida y crea directorios de persistencia
# - Configura permisos correctamente
# - Inicializa la base de datos si no existe
# =============================================================================

set -e  # Salir en caso de error

echo "=========================================="
echo "  Limpiador de Archivos - Iniciando"
echo "=========================================="

# Detectar entorno
if [ -f "/.dockerenv" ] || [ "$IN_DOCKER" = "true" ]; then
    echo "✓ Entorno: Docker"
    DATA_DIR="/app/data"
    IS_DOCKER=true
else
    echo "✓ Entorno: Local"
    # Obtener directorio base del proyecto
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DATA_DIR="$SCRIPT_DIR/data"
    IS_DOCKER=false
fi

echo "✓ Directorio de datos: $DATA_DIR"

# =============================================================================
# CREAR DIRECTORIOS DE PERSISTENCIA
# =============================================================================

echo ""
echo "=== Verificando directorios de persistencia ==="

# Lista de directorios a crear
DIRECTORIES=(
    "$DATA_DIR"
    "$DATA_DIR/backups"
    "/app/static/uploads"
    "/app/static/codes"
)

# En local, también crear en la ruta del proyecto
if [ "$IS_DOCKER" = "false" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    STATIC_DIR="$SCRIPT_DIR/static"
    DIRECTORIES+=(
        "$STATIC_DIR/uploads"
        "$STATIC_DIR/codes"
    )
fi

# Crear directorios si no existen
for DIR in "${DIRECTORIES[@]}"; do
    if [ -d "$DIR" ]; then
        echo "  ✓ Directorio existe: $DIR"
    else
        echo "  + Creando directorio: $DIR"
        mkdir -p "$DIR"
    fi
done

# =============================================================================
# CONFIGURAR PERMISOS
# =============================================================================

echo ""
echo "=== Configurando permisos ==="

if [ "$IS_DOCKER" = "true" ]; then
    # En Docker, asegurar que los directorios sean escribibles
    chmod -R 755 "$DATA_DIR" 2>/dev/null || true
    chmod -R 755 "/app/static/uploads" 2>/dev/null || true
    chmod -R 755 "/app/static/codes" 2>/dev/null || true
    echo "  ✓ Permisos configurados para Docker"
else
    # En local, asegurar permisos de escritura
    chmod -R 755 "$DATA_DIR" 2>/dev/null || true
    chmod -R 755 "$SCRIPT_DIR/static/uploads" 2>/dev/null || true
    chmod -R 755 "$SCRIPT_DIR/static/codes" 2>/dev/null || true
    echo "  ✓ Permisos configurados para entorno local"
fi

# =============================================================================
# INICIALIZAR BASE DE DATOS
# =============================================================================

echo ""
echo "=== Verificando base de datos ==="

DB_PATH="$DATA_DIR/database.db"

if [ -f "$DB_PATH" ]; then
    echo "  ✓ Base de datos encontrada: $DB_PATH"
    
    # Verificar que la base de datos sea accesible
    if sqlite3 "$DB_PATH" "SELECT 1;" > /dev/null 2>&1; then
        echo "  ✓ Base de datos accesible y válida"
    else
        echo "  ⚠ Advertencia: La base de datos parece estar corrupta"
        echo "  ⚠ Se intentará crear una nueva..."
        rm -f "$DB_PATH"
    fi
fi

# Crear base de datos si no existe
if [ ! -f "$DB_PATH" ]; then
    echo "  + Creando nueva base de datos: $DB_PATH"
    
    # Usar Python para crear la base de datos correctamente
    python3 -c "
import sqlite3
import os

db_path = '$DB_PATH'
db_dir = os.path.dirname(db_path)
os.makedirs(db_dir, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('CREATE TABLE IF NOT EXISTS _init_check (id INTEGER PRIMARY KEY)')
conn.execute('DROP TABLE _init_check')
conn.commit()
conn.close()
print('Base de datos creada correctamente')
"
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Base de datos creada exitosamente"
    else
        echo "  ✗ Error al crear la base de datos"
        exit 1
    fi
fi

# =============================================================================
# VALIDAR PERSISTENCIA
# =============================================================================

echo ""
echo "=== Validando persistencia ==="

PERSISTENCE_OK=true

# Verificar que los directorios sean escribibles
for DIR in "$DATA_DIR" "$DATA_DIR/backups" "/app/static/uploads" "/app/static/codes"; do
    if [ -d "$DIR" ] && [ -w "$DIR" ]; then
        : # Directorio escribible
    else
        if [ "$IS_DOCKER" = "false" ] && [[ "$DIR" == *"/static/"* ]]; then
            # En local, estos directorios pueden no existir aún
            continue
        fi
        echo "  ✗ Directorio no escribible: $DIR"
        PERSISTENCE_OK=false
    fi
done

# Verificar base de datos
if [ -f "$DB_PATH" ] && [ -r "$DB_PATH" ] && [ -w "$DB_PATH" ]; then
    echo "  ✓ Base de datos accesible"
else
    echo "  ✗ Base de datos no accesible"
    PERSISTENCE_OK=false
fi

if [ "$PERSISTENCE_OK" = "false" ]; then
    echo ""
    echo "=========================================="
    echo "  ✗ ERROR: No se puede garantizar la persistencia"
    echo "=========================================="
    echo ""
    echo "Por favor verifica que:"
    echo "  - Los volúmenes de Docker estén correctamente montados"
    echo "  - Los permisos de los directorios sean correctos"
    echo ""
    exit 1
fi

echo "  ✓ Persistencia validada correctamente"

# =============================================================================
# INICIAR APLICACIÓN
# =============================================================================

echo ""
echo "=========================================="
echo "  ✓ Iniciando aplicación Flask..."
echo "=========================================="
echo ""

# Exportar variables de entorno para Python
export PYTHONPATH=/app
export IN_DOCKER=$IS_DOCKER

# Iniciar aplicación Flask
exec python app.py
