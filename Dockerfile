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

# Crear directorios necesarios
RUN mkdir -p static/uploads static/codes /app/data /app/data/backups

# Dar permisos al script de inicio
RUN chmod +x start.sh

# Exponer puerto
EXPOSE 5000

# Comando de inicio por defecto
CMD ["python", "-c", "from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000)"]
