"""
Funciones de utilidad y helpers para la aplicación controlStock
"""
from django.shortcuts import render
import logging
import json

logger = logging.getLogger(__name__)


def get_connection_config(request):
    """
    Obtiene IP y Puerto desde:
    1. Sesión (primera prioridad)
    2. Cookies compartidas (segunda prioridad)
    
    Cuando se obtiene desde cookies, se guarda en sesión para optimización.
    
    Args:
        request: HttpRequest object de Django
    
    Returns:
        tupla: (ip, puerto) o (None, None) si no encuentra
    """
    # PRIORIDAD 1: Buscar en sesión de Django
    empresa_ip = request.session.get('empresa_ip')
    empresa_puerto = request.session.get('empresa_puerto')
    
    if empresa_ip and empresa_puerto:
        logger.debug(f"Configuración encontrada en sesión: {empresa_ip}:{empresa_puerto}")
        return empresa_ip, empresa_puerto
    
    # PRIORIDAD 2: Buscar en cookies
    connection_config = request.COOKIES.get('connection_config')
    
    if not connection_config:
        logger.warning("No se encontró cookie 'connection_config'")
        return None, None
    
    try:
        # Decodificar JSON de la cookie
        datos_conexion = json.loads(connection_config)
        
        # Extraer IP y Puerto
        ip = datos_conexion.get('ip')
        puerto = datos_conexion.get('puerto')
        codigo = datos_conexion.get('codigo', '')
        nombre = datos_conexion.get('nombre', '')
        
        # Validar que ambos valores existan y no sean vacíos
        if not ip or not puerto:
            logger.warning(f"IP o Puerto faltantes en connection_config. IP: {ip}, Puerto: {puerto}")
            return None, None
        
        # Convertir puerto a entero si es string
        try:
            puerto = int(puerto) if isinstance(puerto, str) else puerto
        except (ValueError, TypeError):
            logger.error(f"Puerto inválido: {puerto}")
            return None, None
        
        logger.debug(f"Configuración encontrada en cookies: {ip}:{puerto}")
        
        # GUARDAR EN SESIÓN para optimización (importante!)
        request.session['empresa_ip'] = ip
        request.session['empresa_puerto'] = puerto
        if codigo:
            request.session['empresa_codigo'] = codigo
        if nombre:
            request.session['empresa_nombre'] = nombre
        
        logger.debug("Configuración guardada en sesión para futuras consultas")
        
        return ip, puerto
        
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON de connection_config: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Error inesperado al obtener configuración: {e}")
        return None, None


def obtener_datos_cookies(request):
    """
    Obtiene y valida cookies necesarias
    Returns: (token, datos_conexion) o (None, None) si falta algo
    """
    token = request.COOKIES.get('authToken')
    connection_config = request.COOKIES.get('connection_config')
    
    if not token or not connection_config:
        logger.warning("Faltan cookies necesarias")
        return None, None
    
    try:
        datos_conexion = json.loads(connection_config)
        logger.debug(f"Cookies encontradas - Token: {token[:10]}...")
        return token, datos_conexion
    except json.JSONDecodeError:
        logger.error("Error al decodificar connection_config")
        return None, None


def renderizar_error(request, mensaje, empresa_nombre):
    """
    Renderiza página con mensaje de error
    """
    context = {
        'error': True,
        'mensaje': mensaje,
        'empresa_nombre': empresa_nombre
    }
    return render(request, 'landing/landing.html', context)


def renderizar_exito(request, usuario, nombre, empresa_nombre, apps):
    """
    Renderiza landing page con apps disponibles
    """
    context = {
        'error': False,
        'usuario': usuario,
        'nombre': nombre,
        'empresa_nombre': empresa_nombre,
        'apps': apps,
    }
    return render(request, 'landing/landing.html', context)

