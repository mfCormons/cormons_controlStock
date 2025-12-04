"""
Funciones de utilidad y helpers para la aplicación controlStock
"""
from django.shortcuts import render
import logging
import json

logger = logging.getLogger(__name__)


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

