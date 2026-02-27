"""
Utilidades de validación.
Funciones para validar entrada de datos.
"""
import re


def check_dangerous_code(code):
    """
    Verifica si el código contiene patrones peligrosos.
    
    Args:
        code: Código a verificar
        
    Returns:
        tuple: (es_peligroso, mensaje)
    """
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


def validate_module_name(module_name):
    """
    Valida el nombre de un módulo.
    
    Args:
        module_name: Nombre del módulo a validar
        
    Returns:
        bool: True si el nombre es válido
    """
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', module_name))
