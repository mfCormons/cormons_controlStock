"""
Funciones de utilidad y helpers para la aplicación controlStock
"""
from django.shortcuts import render
import logging
import json

logger = logging.getLogger(__name__)


def get_connection_config(request):
    from urllib.parse import unquote

    # Intentar obtener connection_config (JSON)
    connection_config = request.COOKIES.get('connection_config')
    ip = None
    puerto = None

    if connection_config:
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

            if ip and puerto:
                logger.debug(f"Configuración encontrada en connection_config (JSON): {ip}:{puerto}")
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON de connection_config: {e}")
            logger.error(f"Cookie value: {connection_config}")

    # Si no hay connection_config o falló, intentar cookies individuales
    if not ip or not puerto:
        empresa_ip = request.COOKIES.get('empresa_ip')
        empresa_puerto = request.COOKIES.get('empresa_puerto')

        if empresa_ip and empresa_puerto:
            ip = empresa_ip
            puerto = empresa_puerto
            logger.debug(f"Configuración encontrada en cookies individuales: {ip}:{puerto}")
        else:
            logger.warning("No se encontró connection_config ni cookies individuales (empresa_ip, empresa_puerto)")
            return None, None

    # Validar que ambos valores existan y no sean vacíos
    if not ip or not puerto:
        logger.warning(f"IP o Puerto faltantes. IP: {ip}, Puerto: {puerto}")
        return None, None

    # Convertir puerto a entero si es string
    try:
        puerto = int(puerto) if isinstance(puerto, str) else puerto
    except (ValueError, TypeError):
        logger.error(f"Puerto inválido: {puerto}")
        return None, None

    return ip, puerto

def obtener_datos_cookies(request):
    from urllib.parse import unquote

    token = request.COOKIES.get('authToken')
    config = request.COOKIES.get('connection_config')
    usuario = request.COOKIES.get('user_usuario')

    if not token:
        return None, None, None

    # Intentar obtener datos de conexión desde connection_config (JSON)
    datos_conexion = None
    if config:
        try:
            # Decodificar URL encoding antes de parsear JSON
            config_decoded = unquote(config)
            datos_conexion = json.loads(config_decoded)
            print(f"✅ Usando connection_config (JSON)")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando connection_config JSON: {e}")
            print(f"   Config recibido: {config}")

    # Si no hay connection_config o falló el parsing, intentar cookies individuales
    if not datos_conexion:
        empresa_ip = request.COOKIES.get('empresa_ip')
        empresa_puerto = request.COOKIES.get('empresa_puerto')
        empresa_nombre = request.COOKIES.get('empresa_nombre')
        empresa_codigo = request.COOKIES.get('empresa_codigo')

        if empresa_ip and empresa_puerto:
            try:
                datos_conexion = {
                    'ip': empresa_ip,
                    'puerto': int(empresa_puerto),
                    'nombre': unquote(empresa_nombre) if empresa_nombre else '',
                    'codigo': empresa_codigo if empresa_codigo else ''
                }
                print(f"✅ Usando cookies individuales (empresa_ip, empresa_puerto, etc.)")
            except (ValueError, TypeError) as e:
                print(f"❌ Error convirtiendo datos de cookies individuales: {e}")
                return None, None, None
        else:
            print(f"❌ No se encontró connection_config ni cookies individuales válidas")
            return None, None, None

    return token, datos_conexion, usuario


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

