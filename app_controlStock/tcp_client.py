"""
Cliente TCP para comunicación con VFP
Maneja todas las comunicaciones de bajo nivel con el servidor VFP
"""
import logging
import socket
import json
import time
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


def enviar_consulta_tcp_batch(mensajes_list, request=None, ip_custom=None, puerto_custom=None):
    """
    Envía múltiples consultas en batch reutilizando la misma conexión TCP.
    Esto evita el overhead de múltiples connect() que pueden tardar 3+ segundos.

    Args:
        mensajes_list: Lista de diccionarios con los mensajes a enviar
        request: Django request object (para obtener IP/puerto de cookies)
        ip_custom: IP custom (opcional)
        puerto_custom: Puerto custom (opcional)

    Returns:
        Lista de respuestas (diccionarios), una por cada mensaje enviado
    """
    if not TCP_ENABLED:
        return [{"estado": False, "mensaje": "Servicio no disponible"}] * len(mensajes_list)

    # Determinar host/port
    if ip_custom and puerto_custom:
        host, port = ip_custom, int(puerto_custom)
    else:
        host, port = get_connection_config(request)
        if not host or not port:
            return [{"estado": False, "mensaje": "No hay cliente configurado"}] * len(mensajes_list)

    logger.warning(f"Conectando a {host}:{port} para batch de {len(mensajes_list)} mensajes...")
    t_start = time.perf_counter()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TCP_TIMEOUT)

            # CONECTAR UNA SOLA VEZ
            t_connect_start = time.perf_counter()
            s.connect((host, port))
            t_connect_end = time.perf_counter()

            resultados = []

            # ENVIAR CADA MENSAJE Y RECIBIR RESPUESTA (usando la misma conexión)
            for idx, mensaje_dict in enumerate(mensajes_list):
                t_msg_start = time.perf_counter()

                contenido = json.dumps(mensaje_dict, ensure_ascii=False)
                contenido = encriptar(contenido)

                s.sendall(contenido.encode('latin-1', errors='replace'))
                t_sent = time.perf_counter()

                # Recibir respuesta
                respuesta = s.recv(4096)
                t_recv = time.perf_counter()

                if not respuesta:
                    logger.warning(f"Batch[{idx}]: No se recibió respuesta")
                    resultados.append({'estado': False, 'mensaje': 'No se recibió respuesta'})
                    continue

                # Desencriptar y parsear
                respuesta_str_encriptada = respuesta.decode('latin-1')
                respuesta_desencriptada = desencriptar(respuesta_str_encriptada)

                elapsed_msg = t_recv - t_msg_start
                logger.warning(f"Batch[{idx}] ({mensaje_dict.get('Comando', 'unknown')}): {elapsed_msg:.3f}s")

                try:
                    resultado = json.loads(respuesta_desencriptada)
                    resultados.append(resultado)
                except json.JSONDecodeError as e:
                    logger.error(f"Batch[{idx}]: Error parseando JSON: {e}")
                    resultados.append({"estado": False, "mensaje": "Respuesta inválida"})

            # Timing total
            t_end = time.perf_counter()
            elapsed_total = t_end - t_start
            elapsed_connect = t_connect_end - t_connect_start

            logger.warning(f"TCP BATCH timings: connect={elapsed_connect:.3f}s total={elapsed_total:.3f}s mensajes={len(mensajes_list)}")
            print(f"TCP_BATCH_TIMING: connect={elapsed_connect:.3f}s total={elapsed_total:.3f}s count={len(mensajes_list)}")

            return resultados

    except Exception as e:
        logger.exception("ERROR TCP BATCH:")
        return [{"estado": False, "mensaje": str(e)}] * len(mensajes_list)


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

    logger.warning(f"Conectando a {host}:{port} ...")
    t_start = time.perf_counter()

    try:
        contenido = json.dumps(mensaje_dict, ensure_ascii=False)
        contenido = encriptar(contenido)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TCP_TIMEOUT)
            t_connect_start = time.perf_counter()
            s.connect((host, port))
            t_connect_end = time.perf_counter()
            s.sendall(contenido.encode('latin-1', errors='replace'))
            t_sent = time.perf_counter()

            # Intentar leer hasta que el servidor cierre o timeout
            respuesta = s.recv(4096)
            t_recv = time.perf_counter()
            if not respuesta:
                logger.warning("No se recibió respuesta del servidor TCP")
                return {'estado': False, 'mensaje': 'No se recibió respuesta'}

            # CRÍTICO: Convertir bytes a string con latin-1, desencriptar, luego decodificar JSON
            respuesta_str_encriptada = respuesta.decode('latin-1')
            respuesta_desencriptada = desencriptar(respuesta_str_encriptada)

            elapsed_total = t_recv - t_start
            elapsed_connect = t_connect_end - t_connect_start
            elapsed_send_to_recv = t_recv - t_sent
            # Elevar a WARNING para que sea visible en journalctl por defecto
            logger.warning(f"TCP timings: connect={elapsed_connect:.3f}s send_to_recv={elapsed_send_to_recv:.3f}s total={elapsed_total:.3f}s")
            # También imprimir a stdout con prefijo claro por si el logger no aparece
            try:
                print(f"TCP_TIMING: connect={elapsed_connect:.3f}s send_to_recv={elapsed_send_to_recv:.3f}s total={elapsed_total:.3f}s")
            except Exception:
                pass

            try:
                return json.loads(respuesta_desencriptada)
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON: {e}")
                logger.error(f"Respuesta recibida: {repr(respuesta_desencriptada[:200])}")
                return {"estado": False, "mensaje": "Respuesta inválida"}
    except Exception as e:
        logger.exception("ERROR TCP:")
        return {"estado": False, "mensaje": str(e)}
