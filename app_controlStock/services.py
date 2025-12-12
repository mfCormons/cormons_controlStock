"""
Servicios y lógica de negocio para la aplicación controlStock
Incluye llamadas a APIs externas y validaciones
"""
import logging
from datetime import datetime
from .tcp_client import enviar_consulta_tcp
from .__init__ import APP_VERSION

logger = logging.getLogger(__name__)


def formatear_fecha(fecha_str):
    """
    Convierte una fecha en formato ISO (YYYY-MM-DD) o datetime a formato argentino (dd/mm/yyyy)

    Args:
        fecha_str: String en formato ISO, datetime object, o cualquier formato reconocible

    Returns:
        String en formato dd/mm/yyyy o el string original si no se puede parsear
    """
    if not fecha_str:
        return ""

    # Si ya es datetime, convertir directamente
    if isinstance(fecha_str, datetime):
        return fecha_str.strftime("%d/%m/%Y")

    # Intentar parsear diferentes formatos comunes
    formatos = [
        "%Y-%m-%d",           # 2024-12-01
        "%Y-%m-%dT%H:%M:%S",  # 2024-12-01T14:30:00
        "%Y/%m/%d",           # 2024/12/01
        "%d-%m-%Y",           # 01-12-2024
        "%d/%m/%Y",           # 01/12/2024 (ya está en formato correcto)
    ]

    fecha_str = str(fecha_str).strip()

    # Si ya está en formato dd/mm/yyyy, devolverlo tal cual
    if len(fecha_str) == 10 and fecha_str[2] == '/' and fecha_str[5] == '/':
        return fecha_str

    for formato in formatos:
        try:
            fecha_obj = datetime.strptime(fecha_str, formato)
            return fecha_obj.strftime("%d/%m/%Y")
        except ValueError:
            continue

    # Si no se pudo parsear, devolver el string original
    return fecha_str

def comando_verificarToken(token, request):

    mensaje = {
        "Comando": "verificarToken",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "Version": APP_VERSION
    }

    r = enviar_consulta_tcp(mensaje, request=request)

    # Sin respuesta del servidor
    if not r:
        return {
            "estado": False,
            "mensaje": "Sin respuesta del servidor"
        }

    # Si viene estado = false, devolver exactamente lo que vino
    if r.get("estado") is not True:
        return {
            "estado": False,
            "mensaje": r.get("mensaje", "Token inválido")
        }

    # Token válido → devolver datos completos
    return {
        "estado": True,
        "usuario": r.get("usuario", ""),
        "nombre":  r.get("nombre", ""),
        "mensaje": r.get("mensaje", ""),
        "token":   r.get("token", "")
    }


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
    usr = usrActivo if usrActivo is not None else "no definido"

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
                        "fecha": formatear_fecha(fecha)
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
                    "fecha": formatear_fecha(fecha)
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
        "Comando": "RegistrarStockControlado",
        "Token": token,
        "Vista": "CONTROLSTOCK",
        "UsrActivo": usrActivo,
        "idSolicitud": idSolicitud,
        "cantidad": int(cantidad)
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