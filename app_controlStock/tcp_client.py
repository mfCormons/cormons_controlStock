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

            # Leer la respuesta completa en chunks hasta que no haya más datos
            respuesta_completa = b''
            MAX_SIZE = 1024 * 1024  # Límite de 1MB para evitar respuestas infinitas

            while len(respuesta_completa) < MAX_SIZE:
                try:
                    # Después del primer chunk, usar timeout más corto para detectar fin de transmisión
                    if respuesta_completa:
                        s.settimeout(1.5)  # 1.5 segundos para chunks subsiguientes (más generoso)

                    chunk = s.recv(4096)
                    if not chunk:
                        print(f"📭 Recibido chunk vacío. Total acumulado: {len(respuesta_completa)} bytes")
                        break

                    print(f"📦 Chunk recibido: {len(chunk)} bytes. Total: {len(respuesta_completa) + len(chunk)} bytes")
                    respuesta_completa += chunk

                    # NO asumir que es el último solo porque es < 4096
                    # Seguir intentando leer hasta timeout o chunk vacío
                except socket.timeout:
                    # Timeout esperando más datos - asumimos que ya terminó la transmisión
                    print(f"⏱️ Timeout. Bytes acumulados: {len(respuesta_completa)}")
                    if respuesta_completa:
                        break
                    else:
                        return {'estado': False, 'mensaje': 'Timeout esperando respuesta'}

            if not respuesta_completa:
                return {'estado': False, 'mensaje': 'No se recibió respuesta'}

            if len(respuesta_completa) >= MAX_SIZE:
                logger.warning(f"Respuesta muy grande: {len(respuesta_completa)} bytes")
                return {'estado': False, 'mensaje': 'Respuesta demasiado grande'}

            # CRÍTICO: Convertir bytes a string con latin-1, desencriptar, luego decodificar JSON
            print(f"📏 Total de bytes recibidos antes de desencriptar: {len(respuesta_completa)}")

            respuesta_str_encriptada = respuesta_completa.decode('latin-1')
            respuesta_desencriptada = desencriptar(respuesta_str_encriptada)

            print(f"🔓 Respuesta desencriptada (primeros 200 chars): {respuesta_desencriptada[:200]}")
            print(f"🔓 Respuesta desencriptada (últimos 50 chars): {respuesta_desencriptada[-50:]}")

            try:
                return json.loads(respuesta_desencriptada)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parseando JSON: {e}")
                logger.error(f"📄 Respuesta desencriptada (primeros 500 chars): {repr(respuesta_desencriptada[:500])}")
                logger.error(f"📄 Respuesta desencriptada (últimos 100 chars): {repr(respuesta_desencriptada[-100:])}")
                return {"estado": False, "mensaje": "Respuesta inválida"}
    except Exception as e:
        print("ERROR TCP:", repr(e))
        return {"estado": False, "mensaje": str(e)}
