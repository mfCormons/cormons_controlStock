from django.shortcuts import render, redirect
import logging
from django.http import JsonResponse
from .utils import obtener_datos_cookies, renderizar_error, renderizar_exito
from .services import comando_verificarToken, comando_controlPendientes, comando_stockControlado

logger = logging.getLogger(__name__)


def controlStock_view(request):
    
    """
    Vista principal de la control de stock
    Flujo:
    1. Validar cookies
    2. Verificar token
    3. Obtener stock pendientes
    4. Renderizar
    """
    logger.debug("==== CONTROL STOCK VIEW ====")
    
    # PASO 1: Obtener y validar cookies
    token, datos_conexion = obtener_datos_cookies(request)
    #DESCOMENTAR DESPUES DE HARDCODEAR COOKIES
    if not token or not datos_conexion:
        return redirect('http://login.cormonsapp.com/login/')
    
    empresa_nombre = datos_conexion.get('nombre', 'Empresa')
    
    # PASO 2: Verificar token
    respuesta_token = comando_verificarToken(token, request)
    
    if not respuesta_token:
        mensaje = 'Token inválido o expirado'
        return renderizar_error(request, mensaje, empresa_nombre)
    
    # Extraer datos del usuario
    usuario = respuesta_token.get('usuario', respuesta_token.get('Usuario', ''))
    nombre = respuesta_token.get('nombre', respuesta_token.get('Nombre', ''))

    # PASO 3: Obtener apps disponibles
    respuesta_pendientes = comando_controlPendientes(token, request)
    
    if not respuesta_pendientes:
        mensaje = 'Error al obtener stock pendientes'
        return renderizar_error(request, mensaje, empresa_nombre)
    
    pendientes = respuesta_pendientes.get('pendientes', [])
    
    # PASO 4: Renderizar éxito
    # Template real: app_controlStock/templates/app_controlStock/controlStock.html
    return render(request, 'app_controlStock/controlStock.html', {'pendientes': pendientes})
    
def controlPendientes_view(request):
    """
    Endpoint JSON que verifica token y devuelve la lista de pendientes.
    Método: GET
    Cookies requeridas: 'authToken' y 'connection_config' (gestionadas por obtener_datos_cookies)
    """
    # Obtener token y datos de conexión desde cookies
    token, datos_conexion = obtener_datos_cookies(request)
    if not token:
        return JsonResponse({"error": "Faltan cookies de autenticación"}, status=401)

    # Verificar token (usa comando_verificarToken)
    respuesta_token = comando_verificarToken(token, request)
    if not respuesta_token:
        return JsonResponse({"error": "Token inválido o expirado"}, status=401)

    # Obtener pendientes
    respuesta_pendientes = comando_controlPendientes(token, request)
    if not respuesta_pendientes:
        return JsonResponse({"error": "Error al obtener pendientes"}, status=500)

    pendientes = respuesta_pendientes.get("pendientes", [])
    return JsonResponse({"pendientes": pendientes}, status=200)

def logout_view(request):
    """
    Cierra sesión y redirige al login
    """
    logger.debug("==== LOGOUT VIEW CONTROL STOCK ====")
    return redirect('http://login.cormonsapp.com/logout/')