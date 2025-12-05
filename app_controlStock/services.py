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

    # Validar respuesta: aceptar 'Estado' o 'estado'
    estado_raw = None
    if respuesta:
        estado_raw = respuesta.get("Estado", respuesta.get("estado"))
    if not respuesta or not estado_raw:
        mensaje_error = respuesta.get("Mensaje", respuesta.get("mensaje", "Token inválido")) if respuesta else "Error de conexión"
        logger.warning(f"Token inválido: {mensaje_error}")
        return None

    # Normalizar respuesta: soportar 'T'/'F' o booleanos y claves mayúsc/minúsc
    if isinstance(estado_raw, bool):
        estado_bool = estado_raw
    else:
        estado_bool = str(estado_raw).upper() in ("T", "TRUE", "1", "OK")

    respuesta["estado"] = estado_bool
    respuesta["mensaje"] = respuesta.get("Mensaje", respuesta.get("mensaje", ""))
    respuesta["usuario"] = respuesta.get("Usuario", respuesta.get("usuario", ""))
    respuesta["nombre"] = respuesta.get("Nombre", respuesta.get("nombre", ""))
    
    # Validar que el estado sea True
    if not respuesta.get("estado"):
        logger.warning(f"Token inválido: {respuesta.get('mensaje', 'Token inválido')}")
        return None
    
    logger.debug(f"Token válido para: {respuesta.get('usuario')} ({respuesta.get('nombre')})")
    return respuesta

def comando_controlPendientes(token, request, usrActivo=None):
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
    # Usar usrActivo pasado desde la vista (no hardcodear)
    usr = usrActivo if usrActivo is not None else "A"

    mensaje = {
        "Comando": "controlPendientes",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "usrActivo": usr
    }

    logger.info(f"[CONTROLSTOCK] Consultando stock pendientes para token: {token[:10]}... (Version: {APP_VERSION}) (usrActivo: {usr})")
    respuesta = enviar_consulta_tcp(mensaje, request=request)

    # Si no hay respuesta, devolver estructura consistente
    if not respuesta:
        return {"estado": False, "mensaje": "Sin respuesta del servidor", "pendientes": []}

    # Normalizar 'Estado' a booleano
    estado_raw = respuesta.get("Estado", respuesta.get("estado"))
    if isinstance(estado_raw, bool):
        respuesta["estado"] = estado_raw
    else:
        respuesta["estado"] = str(estado_raw).upper() in ("T", "TRUE", "1", "OK")

    # Normalizar mensaje y deposito
    respuesta["mensaje"] = respuesta.get("Mensaje", respuesta.get("mensaje", ""))
    respuesta["deposito"] = respuesta.get("Deposito", respuesta.get("deposito", ""))

    # Obtener lista de pendientes en cualquiera de las variantes de clave
    pendientes_raw = respuesta.get("Pendientes", respuesta.get("PENDIENTES", respuesta.get("pendientes", [])))

    pendientes_normalizados = []
    if isinstance(pendientes_raw, list):
        for item in pendientes_raw:
            # Si el elemento es una lista/tuple posicional, mapear por posición
            if not isinstance(item, dict):
                try:
                    idSolicitud = item[0]
                    codigo = item[1]
                    descripcion = item[2]
                    fecha = item[3] if len(item) > 3 else ""
                    pendientes_normalizados.append({
                        "idSolicitud": idSolicitud,
                        "codigo": codigo,
                        "descripcion": descripcion,
                        "fecha": fecha
                    })
                except Exception:
                    # No se pudo normalizar el elemento, lo omitimos
                    continue
            else:
                # Item es dict: normalizar posibles claves
                idSolicitud = item.get("idSolicitud", item.get("idsolicitud", item.get("IdSolicitud", item.get("IDSOLICITUD", item.get("ID", "")))))
                codigo = item.get("codigo", item.get("Codigo", item.get("CODIGO", "")))
                descripcion = item.get("descripcion", item.get("Descripcion", item.get("DESCRIPCION", "")))
                fecha = item.get("fecha", item.get("Fecha", item.get("FECHA", "")))
                pendientes_normalizados.append({
                    "idSolicitud": idSolicitud,
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "fecha": fecha
                })

    respuesta["pendientes"] = pendientes_normalizados
    return respuesta

def comando_stockControlado(token, request, usrActivo, idSolicitud, cantidad):
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
    mensaje = {
        "Comando": "StockControlado",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "UsrActivo": usrActivo,
        "idSolicitud": idSolicitud,
        "cantidad": cantidad
    }

    logger.info(f"[CONTROLSTOCK] Enviando StockControlado idSolicitud={idSolicitud} cantidad={cantidad} usrActivo={usrActivo}")
    respuesta = enviar_consulta_tcp(mensaje, request=request)

    if not respuesta:
        return {"estado": False, "mensaje": "Sin respuesta del servidor"}

    estado_raw = respuesta.get("Estado", respuesta.get("estado"))
    if isinstance(estado_raw, bool):
        respuesta["estado"] = estado_raw
    else:
        respuesta["estado"] = str(estado_raw).upper() in ("T", "TRUE", "1", "OK")

    respuesta["mensaje"] = respuesta.get("Mensaje", respuesta.get("mensaje", ""))
    return respuesta