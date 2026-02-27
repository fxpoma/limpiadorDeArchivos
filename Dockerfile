# =============================================================================
# Imagen base de Python para Limpiador de Archivos
# =============================================================================
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Definir variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IN_DOCKER=true

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY . .

# =============================================================================
# CREAR DIRECTORIOS DE PERSISTENCIA
# =============================================================================

# Crear estructura de directorios para datos persistentes
# Estos directorios se montarán como volúmenes para persistencia
RUN mkdir -p /app/data/backups \
                /app/static/uploads \
                /app/static/codes \
                /app/logs && \
    # Configurar permisos
    chown -R root:root /app && \
    chmod -R 755 /app && \
    # Hacer directorios de datos escribibles
    chmod -R 777 /app/data /app/static/uploads /app/static/codes

# Crear archivo de base de datos inicial si no existe
RUN python3 -c "\
    import sqlite3, os; \
    os.makedirs('/app/data', exist_ok=True); \
    conn = sqlite3.connect('/app/data/database.db'); \
    conn.execute('CREATE TABLE IF NOT EXISTS _init (id INTEGER PRIMARY KEY)'); \
    conn.execute('PRAGMA journal_mode=WAL'); \
    conn.close(); \
    print('Base de datos inicializada correctamente')"

# Dar permisos al script de inicio
RUN chmod +x start.sh

# =============================================================================
# CONFIGURACIÓN DE PERSISTENCIA
# =============================================================================

# Exponer puerto
EXPOSE 5000

# Definir volúmenes para persistencia (usados por Dokploy)
# IMPORTANTE: Estos volúmenes deben estar montados para que los datos persistan
# - /app/data: base de datos SQLite y backups
# - /app/static/uploads: archivos subidos por usuarios
# - /app/static/codes: códigos guardados
VOLUME ["/app/data", "/app/static/uploads", "/app/static/codes"]

# Configurar variables de entorno para la aplicación
ENV FLASK_RUN_PORT=5000

# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

# Usar script de inicio que valida la persistencia
CMD ["/start.sh"]
