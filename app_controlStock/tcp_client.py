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
    """
    Envía mensaje TCP al servidor externo
    """
    if not TCP_ENABLED:
        logger.warning("TCP está deshabilitado")
        return {"estado": False, "mensaje": "Servicio no disponible"}

    # Determinar IP y Puerto a usar (prioridad: ip_custom/puerto_custom > request > error)
    if ip_custom and puerto_custom:
        # Prioridad 1: Usar IP/Puerto específicos si se proporcionan
        host = ip_custom
        try:
            port = int(puerto_custom) if isinstance(puerto_custom, str) else puerto_custom
        except (ValueError, TypeError):
            logger.error(f"Puerto inválido: {puerto_custom}")
            return {"estado": False, "mensaje": "Puerto inválido"}
        logger.debug(f"Usando IP/Puerto personalizados: {host}:{port}")
    elif request:
        # Prioridad 2: Obtener desde configuración de sesión o cookies
        host, port = get_connection_config(request)
        if not host or not port:
            logger.error("No hay configuración de cliente válida")
            return {"estado": False, "mensaje": "No hay cliente configurado"}
        logger.debug(f"Usando configuración de request: {host}:{port}")
    else:
        logger.error("No se proporcionó configuración de conexión")
        return {"estado": False, "mensaje": "Configuración de conexión requerida"}

    logger.info(f"Realizando consulta TCP a {host}:{port}")
    
    try:
        # Convertir a JSON string
        contenido_json = json.dumps(mensaje_dict, ensure_ascii=False)
        contenido_encriptado = encriptar(contenido_json)
        
        logger.debug(f"Enviando mensaje TCP: {contenido_json}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TCP_TIMEOUT)
            
            logger.debug(f"Conectando a {host}:{port}")
            s.connect((host, port))
            
            # Enviar JSON como bytes UTF-8
            s.sendall(contenido_encriptado.encode('latin-1', errors='replace'))
            logger.debug("JSON enviado correctamente")
            
            # Recibir respuesta
            try:
                respuesta = s.recv(2048)
                if respuesta:
                    respuesta_str = decodificar_respuesta_servidor(respuesta)
                    logger.debug(f"Respuesta recibida: {respuesta_str}")

                    respuesta_desencriptada = desencriptar(respuesta_str)
                    logger.debug(f"Respuesta desencriptada: {respuesta_desencriptada}")                    
                    try:
                        return json.loads(respuesta_desencriptada)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error al decodificar JSON: {e}")
                        return {
                            'estado': False,
                            'mensaje': 'Respuesta inválida del servidor',
                            'respuesta_raw': respuesta_str
                        }
                else:
                    logger.error("No se recibió respuesta del servidor")
                    return {
                        'estado': False,
                        'mensaje': 'No se recibió respuesta del servidor'
                    }
            except socket.timeout:
                logger.error("Tiempo de espera agotado esperando respuesta")
                return {
                    'estado': False,
                    'mensaje': 'Tiempo de espera agotado esperando respuesta'
                }           
            
    except ConnectionRefusedError:
        logger.error(f"El servidor rechazó la conexión en {host}:{port}")
        return {
            'estado': False,
            'mensaje': 'El servidor rechazó la conexión'
        }
    except socket.gaierror as e:
        logger.error(f"Error de resolución de nombre (DNS) para {host}:{port}: {e}")
        return {
            'estado': False,
            'mensaje': f'Error de conexión: No se pudo resolver {host}'
        }
    except OSError as e:
        logger.error(f"Error del sistema operativo en conexión TCP: {e}")
        return {
            'estado': False,
            'mensaje': f'Error de conexión: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Error inesperado en comunicación TCP: {e}", exc_info=True)
        return {
            'estado': False,
            'mensaje': f'Error inesperado: {e}'
        }
