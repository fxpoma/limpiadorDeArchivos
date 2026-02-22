# Imagen base de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Definir variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p static/uploads static/codes

# Exponer puerto
EXPOSE 5000

# Script de inicio
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
