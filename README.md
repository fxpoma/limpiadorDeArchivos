# Limpiador de Archivos - Herramienta de Procesamiento de Archivos

## 🚀 Despliegue con Dokploy

### Requisitos Previos

- Servidor con [Dokploy](https://dokploy.com/) instalado
- Git instalado localmente
- Repositorio Git (GitHub, GitLab, etc.)

### Pasos de Despliegue

1. **Preparar el entorno:**

   ```bash
   # Copiar el archivo de ejemplo de variables de entorno
   cp .env.example .env
   ```

2. **Configurar variables de entorno:**
   Edita el archivo `.env` y establece una `SECRET_KEY` segura:

   ```env
   SECRET_KEY=tu-clave-secreta-aqui
   FLASK_DEBUG=false
   ```

3. **Subir a Git:**

   ```bash
   git add .
   git commit -m "Preparado para despliegue"
   git push origin main
   ```

4. **Configurar en Dokploy:**
   - Accede a tu panel de Dokploy
   - Crea un nuevo proyecto
   - Conecta tu repositorio Git
   - Dokploy detectará automáticamente el archivo `dokploy.yaml`
   - Configura las variables de entorno:
     - `SECRET_KEY`: Tu clave secreta
     - `FLASK_DEBUG`: `false`
   - Despliega el servicio

5. **Acceder a la aplicación:**
   Una vez desplegada, la aplicación estará disponible en el puerto configurado (por defecto 5000).

### Notas

- La base de datos SQLite se persistirá en el volumen configurado
- Los archivos subidos se almacenan en `static/uploads`
- Los códigos Python se guardan en `static/codes`

---

## Descripción

Limpiador de Archivos es una herramienta web que permite a los usuarios procesar archivos mediante códigos Python personalizados de forma segura y eficiente. La aplicación se centra en la privacidad y la seguridad, eliminando cualquier rastro de los archivos procesados en el servidor después de completar el trabajo.

## Características Principales

- **Arrastrar y Soltar**: Interfaz intuitiva para cargar archivos
- **Sistema de Usuarios**: Autenticación con SQLite para identificar usuarios
- **Almacenamiento de Códigos Python**: Guardar y gestionar diferentes scripts de procesamiento
- **Selección de Procesamiento**: Ventana pop-up para elegir el código Python a ejecutar
- **Resultados**: Descarga del archivo procesado o visualización de errores detallados
- **Seguridad**: Eliminación de archivos temporales después del procesamiento
- **Personalización**: Códigos Python con imágenes de previsualización

## Arquitectura del Proyecto

```
limpiadorDeArchivos/
├── app.py                    # Aplicación Flask principal
├── database.py               # Gestión de la base de datos SQLite
├── templates/                # Plantillas HTML
│   ├── base.html             # Plantilla base
│   ├── index.html            # Página principal
│   ├── login.html            # Página de login
│   ├── register.html         # Página de registro
│   ├── profile.html          # Perfil de usuario
│   └── manage_codes.html     # Gestión de códigos Python
├── static/                   # Archivos estáticos
│   ├── css/
│   │   └── style.css         # Estilos CSS
│   ├── js/
│   │   └── script.js         # Scripts JavaScript
│   ├── uploads/              # Archivos temporales (se limpia periódicamente)
│   └── codes/                # Códigos Python guardados
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Documentación del proyecto
```

## Tecnologías Utilizadas

- **Backend**: Python + Flask
- **Base de Datos**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Gestion de Archivos**: Werkzeug
- **Ejecución de Código**: Subprocess
- **Seguridad**: Flask-Login, Flask-Bcrypt

## Instalación y Uso

1. Clonar el repositorio
2. Instalar las dependencias: `pip install -r requirements.txt`
3. Ejecutar la aplicación: `python app.py`
4. Acceder a la aplicación en el navegador: `http://localhost:5000`

## Credenciales de Admin

- **Email:** admin@localhost
- **Contraseña:** admin123

## Proceso de Uso

1. **Registro/Login**: Crear una cuenta o iniciar sesión
2. **Guardar Códigos Python**: Ir al apartado "Gestionar Códigos" y subir scripts
3. **Cargar Archivo**: Arrastrar y soltar el archivo en la interfaz
4. **Seleccionar Procesamiento**: Elegir el código Python a ejecutar en la ventana pop-up
5. **Procesar Archivo**: Esperar a que se complete el procesamiento
6. **Descargar Resultado**: Si el procesamiento es exitoso, descargar el archivo final
7. **Limpieza**: El sistema elimina automáticamente los archivos temporales

---

## NORMAS PARA CREAR CÓDIGOS DE PROCESAMIENTO

### Estructura Obligatoria del Código

Tu código Python debe seguir esta estructura exacta:

```python
import sys

def main():
    # sys.argv[1] contiene la ruta ABSOLUTA del archivo de entrada
    archivo_entrada = sys.argv[1]
    
    # Leer el archivo de entrada y procesarlo
    # ...tu código aquí...
    
    # IMPORTANTE: El archivo de salida debe crearse en el DIRECTORIO ACTUAL
    # No uses sys.argv[2] - el sistema detecta automáticamente el archivo generado
    
    # Ejemplo: crear archivo CSV en el directorio actual
    with open('mi_archivo_salida.csv', 'w', encoding='utf-8') as f:
        f.write('contenido...')

if __name__ == "__main__":
    main()
```

### Normas Claras

#### 1. Argumentos del Sistema

| Variable | Descripción |
|----------|-------------|
| `sys.argv[1]` | Ruta ABSOLUTA del archivo de entrada (archivo subido por el usuario) |

#### 2. Archivo de Salida

- **NO uses `sys.argv[2]`** - El sistema lo ignora
- **Crea el archivo en el directorio actual** (donde se ejecuta el script)
- El sistema detecta automáticamente cualquier archivo nuevo creado
- El nombre del archivo de salida puede ser cualquiera

#### 3. Ubicación del Archivo de Salida

```python
# ✅ CORRECTO: Crear en el directorio actual
with open('resultado.csv', 'w') as f:
    f.write('datos')

# ❌ INCORRECTO: Usar sys.argv[2]
output_file = sys.argv[2]  # NO USAR
```

#### 4. Manejo de Rutas

```python
import sys
import os

# ✅ CORRECTO: Usar la ruta que se pasa como argumento
archivo = sys.argv[1]  # Ruta absoluta al archivo de entrada

# ✅ CORRECTO: Crear archivos en el directorio actual
with open('salida.csv', 'w') as f:
    f.write('...')

# ❌ INCORRECTO: Intentar crear en otra ubicación
with open('/otro/directorio/salida.csv', 'w') as f:
    f.write('...')
```

### Ejemplos de Códigos

#### Ejemplo 1: Convertir CSV a Excel

```python
import sys
import pandas as pd

def main():
    archivo_entrada = sys.argv[1]
    
    # Leer el archivo CSV
    df = pd.read_csv(archivo_entrada)
    
    # Procesar (ejemplo: eliminar filas vacías)
    df = df.dropna()
    
    # Crear archivo de salida en el directorio actual
    df.to_excel('resultado.xlsx', index=False)
    print("Archivo convertido exitosamente")

if __name__ == "__main__":
    main()
```

#### Ejemplo 2: Procesar archivo de texto

```python
import sys

def main():
    archivo_entrada = sys.argv[1]
    
    # Leer archivo
    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Procesar (ejemplo: mayúsculas)
    contenido = contenido.upper()
    
    # Guardar en el directorio actual
    with open('resultado.txt', 'w', encoding='utf-8') as f:
        f.write(contenido)
    print("Procesamiento completado")

if __name__ == "__main__":
    main()
```

#### Ejemplo 3: Convertir Excel a CSV

```python
import sys
import pandas as pd

def main():
    archivo_entrada = sys.argv[1]
    
    # Leer Excel
    df = pd.read_excel(archivo_entrada)
    
    # Guardar como CSV en el directorio actual
    df.to_csv('resultado.csv', index=False, encoding='utf-8')
    print("Conversión completada")

if __name__ == "__main__":
    main()
```

### Notas Importantes

1. **Siempre usa `if __name__ == "__main__":`** para ejecutar tu código
2. **Usa rutas absolutas solo para LEER** el archivo de entrada (`sys.argv[1]`)
3. **Crea archivos de salida en el directorio actual** (no uses sys.argv[2])
4. **Usa `encoding='utf-8'`** para archivos de texto
5. **Evita emojis en print()** - pueden causar errores en Windows
6. **No crees archivos en otras ubicaciones** - solo en el directorio actual

### Códigos NO Permitidos

Por seguridad, el sistema bloquea códigos que contengan:

- `pip install` o `pip3 install`
- `subprocess`, `os.system`, `os.popen`
- `eval()`, `exec()`, `__import__()`
- Comandos de shell como `!pip`, `!conda`
- `import subprocess`

---

## Seguridad

- Todos los archivos se guardan en un directorio temporal con nombres aleatorios
- Los archivos se eliminan después del procesamiento
- Los códigos Python se ejecutan en un entorno seguro
- El acceso a la aplicación requiere autenticación

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue los pasos:

1. Fork del repositorio
2. Crear una rama para la característica: `git checkout -b feature/nueva-caracteristica`
3. Commit de cambios: `git commit -am 'Agregar nueva característica'`
4. Push a la rama: `git push origin feature/nueva-caracteristica`
5. Crear un Pull Request

## Licencia

MIT License - Ver LICENSE.md para más detalles
