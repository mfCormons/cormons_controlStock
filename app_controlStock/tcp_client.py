"""
Cliente TCP para comunicación con VFP
Maneja todas las comunicaciones de bajo nivel con el servidor VFP
"""
import logging
import socket
import json
from .__init__ import APP_VERSION, TCP_TIMEOUT, TCP_ENABLED

logger = logging.getLogger(__name__)    

def enviar_consulta_tcp(mensaje_dict, request=None, ip_custom=None, puerto_custom=None):
    """
    Envía mensaje TCP al servidor externo
    """
    if not TCP_ENABLED:
        logger.warning("TCP está deshabilitado")
        return {"estado": False, "mensaje": "Servicio no disponible"}

    # Determinar IP y Puerto a usar
    if ip_custom and puerto_custom:
        # Usar IP/Puerto específicos
        host = ip_custom
        port = puerto_custom
    elif request:
        # Obtener desde configuración de sesión o cookies
        host, port = get_connection_config(request)
        if not host or not port:
            logger.error("No hay configuración de cliente válida")
            return {"estado": False, "mensaje": "No hay cliente configurado"}
    else:
        logger.error("No se proporcionó configuración de conexión")
        return {"estado": False, "mensaje": "Configuración de conexión requerida"}

    logger.info(f"Realizando consulta TCP a {host}:{port}")
    
    try:
        # Convertir a JSON string
        contenido_json = json.dumps(mensaje_dict, ensure_ascii=False)
        
        logger.debug(f"Enviando mensaje TCP: {contenido_json}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TCP_TIMEOUT)
            
            logger.debug(f"Conectando a {host}:{port}")
            s.connect((host, port))
            
            # Enviar JSON como bytes
            s.sendall(contenido_json.encode('windows-1252', errors='replace'))
            logger.debug("JSON enviado correctamente")
            
            # Recibir respuesta
            try:
                respuesta = s.recv(2048)
                if respuesta:
                    respuesta_str = decodificar_respuesta_servidor(respuesta)
                    logger.debug(f"Respuesta recibida: {respuesta_str}")
                    
                    try:
                        return json.loads(respuesta_str)
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
    except Exception as e:
        logger.error(f"Error inesperado en comunicación TCP: {e}")
        return {
            'estado': False,
            'mensaje': f'Error inesperado: {e}'
        }
    finally:
        logger.debug("Conexión cerrada")
