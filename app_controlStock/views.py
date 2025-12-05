from django.shortcuts import render, redirect
import logging
from django.http import JsonResponse
from .utils import obtener_datos_cookies, renderizar_error, renderizar_exito
from .services import comando_verificarToken, comando_controlPendientes, comando_stockControlado
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
    logger.debug("Obteniendo cookies...")
    token, datos_conexion = obtener_datos_cookies(request)
    logger.debug(f"Token obtenido: {token[:10] if token else 'None'}")
    logger.debug(f"Datos de conexión: {datos_conexion}")
    #DESCOMENTAR DESPUES DE HARDCODEAR COOKIES
    if not token or not datos_conexion:
        return redirect('http://login.cormonsapp.com/login/')
    
    logger.debug("Cookies válidas.")
    
    empresa_nombre = datos_conexion.get('nombre', 'Empresa')
    
    # Si es la primera vez que el usuario llega a la URL raíz, debemos
    # verificar el token y guardar usuario/nombre en session.
    usuario = request.session.get('usuario')
    nombre = request.session.get('nombre')
    if not usuario or not nombre:
        # Ejecutar verificarToken una sola vez al llegar
        respuesta_token = comando_verificarToken(token, request)
        if not respuesta_token:
            # Token inválido: redirigir al login
            return redirect('http://login.cormonsapp.com/login/')
        usuario = respuesta_token.get('usuario', 'A')
        nombre = respuesta_token.get('nombre', 'Usuario')
        # Guardar en session para posteriores acciones (actualizar/modal-close)
        request.session['usuario'] = usuario
        request.session['nombre'] = nombre

    # PASO 3: Obtener apps disponibles
    # Obtener pendientes usando el usuario activo de la sesión
    respuesta_pendientes = comando_controlPendientes(token, request, usrActivo=usuario)

    if not respuesta_pendientes:
        mensaje = 'Error al obtener stock pendientes'
        return renderizar_error(request, mensaje, empresa_nombre)

    # Normalizar distintas formas de respuesta desde VFP
    pendientes = []
    # Preferir campo 'pendientes' si está presente
    if isinstance(respuesta_pendientes.get('pendientes'), list) and respuesta_pendientes.get('pendientes'):
        pendientes = respuesta_pendientes.get('pendientes')
    # Soportar respuestas con 'PRODUCTOS' (temporal/provisoria)
    elif isinstance(respuesta_pendientes.get('PRODUCTOS'), list) and respuesta_pendientes.get('PRODUCTOS'):
        productos = respuesta_pendientes.get('PRODUCTOS')
        # Mapear cada producto a un dict con claves esperadas por la plantilla
        pendientes = []
        for p in productos:
            pendientes.append({
                'idSolicitud': p.get('idSolicitud', ''),
                'codigo': p.get('codigo') or p.get('cod') or '',
                'descripcion': p.get('descripcion') or p.get('desc') or '',
                'fecha': p.get('fecha', '')
            })
    else:
        # Fallback: intentar otros campos posibles
        for key in ('PENDIENTES', 'productos', 'PRODUCTOS'):
            val = respuesta_pendientes.get(key)
            if isinstance(val, list) and val:
                pendientes = val
                break
    
    # PASO 4: Renderizar éxito
    # al final de controlStock_view, en lugar de lo actual:
    context = {
        'pendientes': pendientes,
        'empresa_nombre': empresa_nombre,
        'usuario': usuario,
        'nombre': nombre,
        # opcional: pasar datos adicionales devueltos por controlPendientes
        'deposito': respuesta_pendientes.get('deposito', ''),
        'cod_deposito': respuesta_pendientes.get('cod_deposito', ''),
    }
    return render(request, 'app_controlStock/controlStock.html', context)
    
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

    # Para las acciones UI (botón actualizar, cerrar modal) NO debemos
    # ejecutar verificarToken de nuevo. Usamos el usuario guardado en session
    usuario = request.session.get('usuario')
    if not usuario:
        return JsonResponse({"error": "Sesión inválida - reingrese"}, status=401)

    respuesta_pendientes = comando_controlPendientes(token, request, usrActivo=usuario)
    if not respuesta_pendientes:
        return JsonResponse({"error": "Error al obtener pendientes"}, status=500)

    pendientes = respuesta_pendientes.get("pendientes", [])
    return JsonResponse({"pendientes": pendientes}, status=200)


@csrf_exempt
@require_POST
def stockControlado_view(request):
    """
    Endpoint que recibe POST con idSolicitud y cantidad, llama comando_stockControlado y responde JSON.
    Espera JSON: {token, idSolicitud, cantidad}
    """
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"estado": False, "mensaje": "JSON inválido"}, status=400)

    token = data.get('token')
    idSolicitud = data.get('idSolicitud')
    cantidad = data.get('cantidad')
    if not token or not idSolicitud or cantidad is None:
        return JsonResponse({"estado": False, "mensaje": "Faltan datos obligatorios"}, status=400)

    usuario = request.session.get('usuario')
    if not usuario:
        return JsonResponse({"estado": False, "mensaje": "Sesión expirada. Reingrese."}, status=401)

    respuesta = comando_stockControlado(token, request, usuario, idSolicitud, cantidad)
    return JsonResponse({"estado": respuesta.get('estado', False), "mensaje": respuesta.get('mensaje', '')})

def logout_view(request):
    """
    Cierra sesión y redirige al login
    """
    logger.debug("==== LOGOUT VIEW CONTROL STOCK ====")
    return redirect('http://login.cormonsapp.com/logout/')