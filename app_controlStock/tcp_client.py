"""
Cliente TCP para comunicación con VFP
Maneja todas las comunicaciones de bajo nivel con el servidor VFP
"""
import logging
import socket
import json
from .__init__ import APP_VERSION, TCP_TIMEOUT, TCP_ENABLED
from .utils import get_connection_config
from .algoritmoEncriptacionCasero import encriptar, desencriptar

logger = logging.getLogger(__name__)


def decodificar_respuesta_servidor(respuesta_bytes):
    """
    Decodifica respuesta del servidor intentando múltiples codificaciones.
    
    Args:
        respuesta_bytes: Bytes recibidos del servidor
    
    Returns:
        str: String decodificado
    """
    codificaciones = ['utf-8', 'windows-1252', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for codificacion in codificaciones:
        try:
            respuesta_str = respuesta_bytes.decode(codificacion)
            logger.debug(f"Respuesta decodificada con {codificacion}")
            return respuesta_str
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Si ninguna codificación funciona, usar 'replace' para evitar errores
    logger.warning("No se pudo decodificar con ninguna codificación estándar, usando 'replace'")
    return respuesta_bytes.decode('utf-8', errors='replace')


def enviar_consulta_tcp(mensaje_dict, request=None, ip_custom=None, puerto_custom=None):

    if not TCP_ENABLED:
        return {"estado": False, "mensaje": "Servicio no disponible"}

    # Determinar host/port
    if ip_custom and puerto_custom:
        host, port = ip_custom, int(puerto_custom)
    else:
        host, port = get_connection_config(request)
        if not host or not port:
            return {"estado": False, "mensaje": "No hay cliente configurado"}

    print(f"Conectando a {host}:{port} ...")

    try:
        contenido = json.dumps(mensaje_dict, ensure_ascii=False)
        contenido = encriptar(contenido)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TCP_TIMEOUT)
            s.connect((host, port))
            s.sendall(contenido.encode('latin-1', errors='replace'))

            respuesta = s.recv(2048)
            if not respuesta:
                return {'estado': False, 'mensaje': 'No se recibió respuesta'}

            # CRÍTICO: Convertir bytes a string con latin-1, desencriptar, luego decodificar JSON
            respuesta_str_encriptada = respuesta.decode('latin-1')
            respuesta_desencriptada = desencriptar(respuesta_str_encriptada)

            try:
                return json.loads(respuesta_desencriptada)
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON: {e}")
                logger.error(f"Respuesta recibida: {repr(respuesta_desencriptada[:200])}")
                return {"estado": False, "mensaje": "Respuesta inválida"}
    except Exception as e:
        print("ERROR TCP:", repr(e))
        return {"estado": False, "mensaje": str(e)}
