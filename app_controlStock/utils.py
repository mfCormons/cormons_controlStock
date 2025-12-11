"""
Funciones de utilidad y helpers para la aplicación controlStock
"""
from django.shortcuts import render
import logging
import json

logger = logging.getLogger(__name__)


def get_connection_config(request):
    from urllib.parse import unquote
    
    # PRIORIDAD 1: Buscar en sesión de Django
    #empresa_ip = request.session.get('empresa_ip')
    #empresa_puerto = request.session.get('empresa_puerto')

    # No permitir localhost si la cookie trae otra IP
    #if empresa_ip and empresa_puerto and empresa_ip != "127.0.0.1":
        #return empresa_ip, empresa_puerto
    
    #if empresa_ip and empresa_puerto:
        #logger.debug(f"Configuración encontrada en sesión: {empresa_ip}:{empresa_puerto}")
        #return empresa_ip, empresa_puerto
    
    # PRIORIDAD 2: Buscar en cookies
    connection_config = request.COOKIES.get('connection_config')
    
    if not connection_config:
        logger.warning("No se encontró cookie 'connection_config'")
        return None, None
    
    try:
        # DECODIFICAR URL antes de parsear JSON
        connection_config_decoded = unquote(connection_config)
        
        # Decodificar JSON de la cookie
        datos_conexion = json.loads(connection_config_decoded)
        
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
        
        # GUARDAR EN SESIÓN para optimización
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
        logger.error(f"Cookie value: {connection_config}")
        return None, None
    except Exception as e:
        logger.error(f"Error inesperado al obtener configuración: {e}")
        return None, None

def obtener_datos_cookies(request):
    from urllib.parse import unquote

    token = request.COOKIES.get('authToken')
    config = request.COOKIES.get('connection_config')
    usuario = request.COOKIES.get('user_usuario')

    if not token or not config:
        return None, None, None

    if not usuario or usuario.strip() == '':
        return None, None, None

    try:
        # Decodificar URL encoding antes de parsear JSON
        config_decoded = unquote(config)
        return token, json.loads(config_decoded), usuario
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {e}")
        print(f"   Config recibido: {config}")
        print(f"   Config decoded: {config_decoded if 'config_decoded' in locals() else 'N/A'}")
        return None, None, None


def renderizar_error(request, mensaje, empresa_nombre='', redirect_to=None, redirect_delay=5):
    """
    Renderiza página con mensaje de error

    Args:
        mensaje: Mensaje de error a mostrar
        empresa_nombre: Nombre de la empresa (opcional)
        redirect_to: URL a la que redirigir después del delay (opcional)
        redirect_delay: Segundos antes de redirigir (default: 5)
    """
    context = {
        'error': True,
        'mensaje': mensaje,
        'empresa_nombre': empresa_nombre,
        'redirect_to': redirect_to,
        'redirect_delay': redirect_delay
    }
    return render(request, 'app_controlStock/controlStock.html', context)


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
    return render(request, 'app_controlStock/controlStock.html', context)

