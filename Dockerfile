# Imagen base de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Definir variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IN_DOCKER=true

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p static/uploads static/codes /app/data /app/data/backups && \
    chown -R root:root /app && \
    chmod -R 755 /app

# Crear archivo de base de datos inicial si no existe
RUN touch /app/data/database.db && \
    chmod 666 /app/data/database.db

# Dar permisos al script de inicio
RUN chmod +x start.sh

# Exponer puerto
EXPOSE 5000

# Definir volúmenes para persistencia (usados por Dokploy)
# - /app/data: base de datos SQLite y backups
# - /app/static/uploads: archivos subidos por usuarios
# - /app/static/codes: códigos guardados
VOLUME ["/app/data", "/app/static/uploads", "/app/static/codes"]

# Comando de inicio por defecto
CMD ["python", "-c", "from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000)"]
