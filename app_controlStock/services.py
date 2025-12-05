"""
Servicios y lógica de negocio para la aplicación controlStock
Incluye llamadas a APIs externas y validaciones
"""
import logging
from .tcp_client import enviar_consulta_tcp
from .__init__ import APP_VERSION

logger = logging.getLogger(__name__)

def comando_verificarToken(token, request):
    """
    Verifica si el token es válido con VFP
    Returns: dict con datos del usuario si es válido, None si falla
    """
    logger.debug("dentro de comando_verificarToken...")
    
    # Preparar mensaje
    mensaje = {
        "Comando": "verificarToken",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "Version": APP_VERSION
    }
    
    logger.info(f"[CONTROLSTOCK] Verificando token: {token[:10] if token else 'None'}... (Version: {APP_VERSION})")
    
    # Enviar consulta TCP
    respuesta = enviar_consulta_tcp(mensaje, request=request)
    logger.debug(f"Respuesta recibida: {respuesta}")
    
    # Validar respuesta
    if not respuesta or not respuesta.get("estado"):
        mensaje_error = respuesta.get("Mensaje", "Token inválido") if respuesta else "Error de conexión"
        logger.warning(f"Token inválido: {mensaje_error}")
        return None
    
    # Normalizar respuesta (Estado "T"/"F" a booleano)
    respuesta["estado"] = respuesta["Estado"] == "T"
    respuesta["mensaje"] = respuesta.get("Mensaje", "")
    respuesta["usuario"] = respuesta.get("Usuario", "")
    respuesta["nombre"] = respuesta.get("Nombre", "")
    
    # Validar que el estado sea True
    if not respuesta.get("estado"):
        logger.warning(f"Token inválido: {respuesta.get('mensaje', 'Token inválido')}")
        return None
    
    logger.debug(f"Token válido para: {respuesta.get('usuario')} ({respuesta.get('nombre')})")
    return respuesta

def comando_controlPendientes(token, request):
    """
    Solicitud (App → VFP)
    {
    "Comando": "controlPendientes",
    "Token": "123abc456def",
    "Vista": "CONTROLSTOCK",
    "usrActivo": "usuario123"
    }

    Respuesta (VFP → App)
    {
    "Estado": "T",
    "Mensaje": "",
    "Deposito": "",
    "Pendientes": [idSolicitud, cod, descripcion]
    }

    o
    {
        "Estado": "F",
        "Mensaje": "Token inválido"
    }
    """
    mensaje = {
        "Comando": "controlPendientes",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "usrActivo": "usuarioPrueba"
    }
    
    logger.info(f"[CONTROLSTOCK] Consultando stock pendientes para token: {token[:10]}... (Version: {APP_VERSION})")
    respuesta = enviar_consulta_tcp(mensaje, request=request)
    
    # Convertir Estado "T"/"F" a booleano para compatibilidad interna
    if respuesta and "Estado" in respuesta:
        respuesta["estado"] = respuesta["Estado"] == "T"
        respuesta["mensaje"] = respuesta.get("Mensaje", "")
        respuesta["pendientes"] = respuesta.get("Pendientes", [])
    
    return respuesta

def comando_stockControlado(token, request):
    """
    Debo enviar esta estructura de datos a VFP (App → VFP)
    {
    "comando": "StockControlado",
    "token": "123abc",
    "Vista": "CONTROLSTOCK",
    “UsrActivo”:”A”,
    "idSolicitud": idSolicitud,
    "cantidad": cantidad,
    }"

    """
    
    return respuesta