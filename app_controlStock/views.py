from django.shortcuts import render, redirect
import logging
from django.http import JsonResponse
#from compartidos.cookies_utils import sincronizar_conexion_a_sesion
from .utils import obtener_datos_cookies, renderizar_error, renderizar_exito
from .services import comando_verificarToken, comando_controlPendientes, comando_stockControlado
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


logger = logging.getLogger(__name__)

def setup_mock(request):
    """Vista para setear cookies en desarrollo - NO requiere autenticación"""
    from django.http import HttpResponse

    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup Mock Cookies</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
        .checkbox-group { display: flex; align-items: center; gap: 10px; }
        .checkbox-group input[type="checkbox"] { width: auto; }
        button { background: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; margin-top: 10px; }
        button:hover { background: #218838; }
        .btn-danger { background: #dc3545; margin-top: 5px; }
        .btn-danger:hover { background: #c82333; }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; margin-top: 20px; display: none; }
        .info { background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .warning { background: #fff3cd; color: #856404; padding: 15px; border-radius: 4px; margin-top: 15px; }
        code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .section-title { background: #e9ecef; padding: 10px; border-radius: 4px; margin-top: 20px; margin-bottom: 15px; font-weight: bold; }
        .cookie-status { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Setup Mock Cookies - Testing</h1>

        <div class="info">
            <strong>⚠️ Instrucciones:</strong><br>
            1. Inicia el servidor mock: <code>python mock_vfp_server.py</code><br>
            2. Marca las cookies que quieres setear<br>
            3. Completa los campos habilitados<br>
            4. Haz clic en "Setear Cookies"<br>
            5. Ve a: <code>http://localhost:8000/</code>
        </div>

        <form id="cookieForm">
            <div class="section-title">🔑 Autenticación</div>

            <div class="form-group checkbox-group">
                <input type="checkbox" id="enableToken" checked>
                <label for="enableToken" style="margin: 0;">Setear Token (authToken)</label>
            </div>
            <div class="form-group">
                <label>Token de Autenticación:</label>
                <input type="text" id="token" value="123abc456def">
            </div>

            <div class="section-title">👤 Usuario</div>

            <div class="form-group checkbox-group">
                <input type="checkbox" id="enableUsuario" checked>
                <label for="enableUsuario" style="margin: 0;">Setear Usuario (user_usuario)</label>
            </div>
            <div class="form-group">
                <label>Usuario:</label>
                <input type="text" id="usuario" value="jperez">
            </div>

            <div class="form-group checkbox-group">
                <input type="checkbox" id="enableNombre" checked>
                <label for="enableNombre" style="margin: 0;">Setear Nombre (user_nombre)</label>
            </div>
            <div class="form-group">
                <label>Nombre Completo:</label>
                <input type="text" id="nombreUsuario" value="Juan Pérez">
            </div>

            <div class="section-title">🏢 Conexión VFP</div>

            <div class="form-group checkbox-group">
                <input type="checkbox" id="enableConnection" checked>
                <label for="enableConnection" style="margin: 0;">Setear Conexión (connection_config)</label>
            </div>

            <div class="form-group">
                <label>IP del Servidor VFP:</label>
                <input type="text" id="ip" value="127.0.0.1">
            </div>

            <div class="form-group">
                <label>Puerto del Servidor VFP:</label>
                <input type="number" id="puerto" value="5555">
            </div>

            <div class="form-group">
                <label>Nombre de Empresa:</label>
                <input type="text" id="nombre" value="Empresa Demo S.A.">
            </div>

            <div class="form-group">
                <label>Código de Empresa:</label>
                <input type="text" id="codigo" value="EMP001">
            </div>

            <button type="submit">🍪 Setear Cookies Seleccionadas</button>
            <button type="button" class="btn-danger" onclick="clearAllCookies()">🗑️ Borrar TODAS las Cookies</button>
        </form>

        <div class="success" id="successMsg">
            ✅ Cookies seteadas correctamente!<br>
            Ahora puedes ir a: <a href="/">Control Stock</a>
        </div>

        <div class="warning">
            <strong>💡 Escenarios de prueba:</strong><br>
            • Sin token: Desmarca "Setear Token"<br>
            • Sin usuario: Desmarca "Setear Usuario"<br>
            • Sin conexión: Desmarca "Setear Conexión"<br>
            • Usuario vacío: Marca "Setear Usuario" pero deja el campo vacío
        </div>

        <div class="section-title">📋 Estado Actual de Cookies</div>
        <div class="cookie-status" id="cookieStatus"></div>
    </div>

    <script>
        // Actualizar estado de cookies al cargar
        updateCookieStatus();

        // Habilitar/deshabilitar campos según checkboxes
        document.getElementById('enableToken').addEventListener('change', function() {
            document.getElementById('token').disabled = !this.checked;
        });
        document.getElementById('enableUsuario').addEventListener('change', function() {
            document.getElementById('usuario').disabled = !this.checked;
        });
        document.getElementById('enableNombre').addEventListener('change', function() {
            document.getElementById('nombreUsuario').disabled = !this.checked;
        });
        document.getElementById('enableConnection').addEventListener('change', function() {
            document.getElementById('ip').disabled = !this.checked;
            document.getElementById('puerto').disabled = !this.checked;
            document.getElementById('nombre').disabled = !this.checked;
            document.getElementById('codigo').disabled = !this.checked;
        });

        document.getElementById('cookieForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const enableToken = document.getElementById('enableToken').checked;
            const enableUsuario = document.getElementById('enableUsuario').checked;
            const enableNombre = document.getElementById('enableNombre').checked;
            const enableConnection = document.getElementById('enableConnection').checked;

            // Setear token si está habilitado
            if (enableToken) {
                const token = document.getElementById('token').value;
                document.cookie = `authToken=${token}; path=/; max-age=3600`;
                console.log('✅ authToken seteado:', token);
            }

            // Setear usuario si está habilitado
            if (enableUsuario) {
                const usuario = document.getElementById('usuario').value;
                document.cookie = `user_usuario=${usuario}; path=/; max-age=3600`;
                console.log('✅ user_usuario seteado:', usuario);
            }

            // Setear nombre si está habilitado
            if (enableNombre) {
                const nombreUsuario = document.getElementById('nombreUsuario').value;
                document.cookie = `user_nombre=${encodeURIComponent(nombreUsuario)}; path=/; max-age=3600`;
                console.log('✅ user_nombre seteado:', nombreUsuario);
            }

            // Setear conexión si está habilitado
            if (enableConnection) {
                const ip = document.getElementById('ip').value;
                const puerto = document.getElementById('puerto').value;
                const nombre = document.getElementById('nombre').value;
                const codigo = document.getElementById('codigo').value;

                const connectionConfig = {
                    ip: ip,
                    puerto: parseInt(puerto),
                    nombre: nombre,
                    codigo: codigo
                };

                // Setear ambos formatos: JSON y cookies individuales
                document.cookie = `connection_config=${encodeURIComponent(JSON.stringify(connectionConfig))}; path=/; max-age=3600`;
                document.cookie = `empresa_ip=${ip}; path=/; max-age=3600`;
                document.cookie = `empresa_puerto=${puerto}; path=/; max-age=3600`;
                document.cookie = `empresa_nombre=${encodeURIComponent(nombre)}; path=/; max-age=3600`;
                document.cookie = `empresa_codigo=${codigo}; path=/; max-age=3600`;
                console.log('✅ connection_config seteado (JSON + cookies individuales):', connectionConfig);
            }

            document.getElementById('successMsg').style.display = 'block';
            updateCookieStatus();

            setTimeout(() => {
                document.getElementById('successMsg').style.display = 'none';
            }, 3000);
        });

        function clearAllCookies() {
            const cookies = ['authToken', 'user_usuario', 'user_nombre', 'connection_config', 'empresa_ip', 'empresa_puerto', 'empresa_nombre', 'empresa_codigo'];
            cookies.forEach(cookie => {
                document.cookie = `${cookie}=; path=/; max-age=0`;
            });
            console.log('🗑️ Todas las cookies borradas');
            alert('🗑️ Todas las cookies han sido borradas');
            updateCookieStatus();
        }

        function updateCookieStatus() {
            const cookieStatus = document.getElementById('cookieStatus');
            const cookies = document.cookie.split(';').map(c => c.trim()).filter(c => c);

            if (cookies.length === 0) {
                cookieStatus.innerHTML = '<em style="color: #999;">No hay cookies seteadas</em>';
            } else {
                cookieStatus.innerHTML = cookies.map(cookie => {
                    const [name, ...valueParts] = cookie.split('=');
                    const value = valueParts.join('=');
                    return `<strong>${name}:</strong> ${value}`;
                }).join('<br>');
            }
        }

        // Actualizar estado cada 2 segundos
        setInterval(updateCookieStatus, 2000);
    </script>
</body>
</html>'''

    return HttpResponse(html)

def controlStock_view(request):
    import time
    t_view_start = time.perf_counter()
    logger.debug("==== CONTROL STOCK VIEW INICIANDO ====")

    # 1) Cookies
    token, datos_conexion, usuario_cookie = obtener_datos_cookies(request)

    print(f"🔑 Token obtenido: {token}")
    print(f"📦 Datos conexion: {datos_conexion}")
    print(f"👤 Usuario cookie: {usuario_cookie}")

    # Obtener nombre de empresa para mensajes de error
    empresa_nombre = datos_conexion.get('nombre', '') if datos_conexion else ''

    if not token or not datos_conexion:
        print("❌ REDIRIGIENDO - No hay token o datos de conexión")
        return renderizar_error(
            request,
            "No se encontraron credenciales de autenticación",
            empresa_nombre,
            redirect_to='https://login.cormons.app/',
            redirect_delay=5
        )

    if not usuario_cookie:
        print("❌ REDIRIGIENDO - No hay usuario activo")
        return renderizar_error(
            request,
            "No hay usuario activo. Por favor, inicie sesión nuevamente.",
            empresa_nombre,
            redirect_to='https://login.cormons.app/',
            redirect_delay=5
        )

    empresa_nombre = datos_conexion.get('nombre', 'EmpresaDefault')

    print(f"✅ Token y datos OK - verificando con VFP...")

    # 2) Verificar token
    t_verificar_start = time.perf_counter()
    verificarToken = comando_verificarToken(token, request)
    t_verificar_end = time.perf_counter()
    logger.info(f"📡 Respuesta verificarToken: {verificarToken} (duracion: {t_verificar_end - t_verificar_start:.3f}s)")

    if not verificarToken["estado"]:
        mensaje = verificarToken.get("mensaje", "Token inválido")
        # Limpiar sesión
        request.session.flush()
        # Mostrar error y redirigir después de 5 segundos
        return renderizar_error(request, mensaje, empresa_nombre, redirect_to='https://login.cormons.app/', redirect_delay=5)

    usuario = verificarToken["usuario"]
    nombre = verificarToken["nombre"]

    request.session['usuario'] = usuario
    request.session['nombre'] = nombre

    print(f"✅ Usuario verificado: {usuario}")

    # 3) Consultar pendientes
    t_pend_start = time.perf_counter()
    respuesta = comando_controlPendientes(token, request, usrActivo=usuario)
    t_pend_end = time.perf_counter()
    logger.info(f"📡 Respuesta controlPendientes (duracion: {t_pend_end - t_pend_start:.3f}s)")
    if not respuesta:
        return renderizar_error(request, "Error al obtener stock pendientes", empresa_nombre)

    # Verificar si VFP respondió con error
    if respuesta.get("estado") is False:
        mensaje = respuesta.get("mensaje", "Error al obtener stock pendientes")
        # Limpiar sesión
        request.session.flush()
        # Mostrar error y redirigir después de 5 segundos
        return renderizar_error(request, mensaje, empresa_nombre, redirect_to='https://login.cormons.app/', redirect_delay=5)

    # 4) Normalizar productos
    pendientes = (
        respuesta.get("pendientes")
        or respuesta.get("PRODUCTOS")
        or respuesta.get("productos")
        or respuesta.get("PENDIENTES")
        or []
    )

    # 5) Render
    t_view_end = time.perf_counter()
    logger.info(f"CONTROL STOCK VIEW total duration: {t_view_end - t_view_start:.3f}s")
    return render(request, "app_controlStock/controlStock.html", {
        "pendientes": pendientes,
        "empresa_nombre": empresa_nombre,
        "usuario": usuario,
        "nombre": nombre,
        "deposito": respuesta.get("deposito", ""),
        "error": False,
    })


def controlPendientes_view(request):
    """
    Endpoint JSON que verifica token y devuelve la lista de pendientes.
    Método: GET
    Cookies requeridas: 'authToken', 'connection_config' y 'user_usuario' (gestionadas por obtener_datos_cookies)
    """
    # Obtener token, datos de conexión y usuario desde cookies
    token, datos_conexion, usuario_cookie = obtener_datos_cookies(request)
    if not token or not usuario_cookie:
        return JsonResponse({
            "error": "No hay usuario activo",
            "redirect": "https://login.cormons.app/"
        }, status=401)

    # Para las acciones UI (botón actualizar, cerrar modal) NO debemos
    # ejecutar verificarToken de nuevo. Usamos el usuario guardado en session
    usuario = request.session.get('usuario')
    if not usuario:
        return JsonResponse({"error": "Sesión inválida - reingrese"}, status=401)

    respuesta_pendientes = comando_controlPendientes(token, request, usrActivo=usuario)
    if not respuesta_pendientes:
        return JsonResponse({"error": "Error al obtener pendientes"}, status=500)

    # Verificar si VFP respondió con error (token inválido, versión incorrecta, etc.)
    if respuesta_pendientes.get("estado") is False:
        # Limpiar sesión
        request.session.flush()
        # Retornar 401 incluyendo el mensaje devuelto por VFP para que el frontend
        # pueda mostrar el detalle exacto antes de redirigir.
        mensaje_vfp = respuesta_pendientes.get('mensaje', 'Sesión inválida')
        return JsonResponse({
            "error": mensaje_vfp,
            "redirect": "https://login.cormons.app/"
        }, status=401)

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

    # Limpiar comillas extras del token
    if token:
        token = token.strip().strip('"').strip("'")
        #print(f"🔧 Token limpiado: {repr(token)}")

    idSolicitud = data.get('idSolicitud')
    cantidad = data.get('cantidad')
    if not token or not idSolicitud or cantidad is None:
        return JsonResponse({"estado": False, "mensaje": "Faltan datos obligatorios"}, status=400)

    usuario = request.session.get('usuario')
    if not usuario:
        return JsonResponse({"estado": False, "mensaje": "Sesión expirada. Reingrese."}, status=401)

    respuesta = comando_stockControlado(token, request, usuario, idSolicitud, cantidad)

    estado = respuesta.get('estado', False)
    mensaje = respuesta.get('mensaje', '')

    # Verificar si VFP respondió con error (token inválido, versión incorrecta, etc.)
    if estado is False:
        # Limpiar sesión
        request.session.flush()
        # Retornar 401 para que el frontend redirija al login
        return JsonResponse({
            "error": mensaje or "Error al registrar control",
            "redirect": "https://login.cormons.app/"
        }, status=401)

    # Si es exitoso pero no hay mensaje, usar mensaje por defecto
    if estado and not mensaje:
        mensaje = 'Stock controlado correctamente'

    return JsonResponse({"estado": estado, "mensaje": mensaje})

def logout_view(request):
    """
    Cierra sesión del usuario actual: limpia sesión y cookies de usuario,
    y redirige al login
    """
    logger.debug("==== LOGOUT VIEW CONTROL STOCK ====")

    # Limpiar sesión de Django (usuario, nombre, empresa_ip, empresa_puerto, etc.)
    request.session.flush()

    # Redirigir al login
    response = redirect('https://login.cormons.app/')

    # Borrar SOLO cookies de usuario (mantiene authToken y connection_config)
    response.delete_cookie('user_nombre', domain='.cormons.app')
    response.delete_cookie('user_usuario', domain='.cormons.app')

    logger.debug("Cookies de usuario borradas, redirigiendo a login")

    return response
