from django.shortcuts import render, redirect
import logging
from django.http import JsonResponse
from .utils import obtener_datos_cookies, renderizar_error, renderizar_exito
from .services import comando_verificarToken, comando_controlPendientes, comando_stockControlado
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        button { background: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; margin-top: 10px; }
        button:hover { background: #218838; }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; margin-top: 20px; display: none; }
        .info { background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Setup Mock Cookies</h1>
        
        <div class="info">
            <strong>⚠️ Instrucciones:</strong><br>
            1. Inicia el servidor mock: <code>python mock_vfp_server.py</code><br>
            2. Completa este formulario<br>
            3. Haz clic en "Setear Cookies"<br>
            4. Ve a: <code>http://localhost:8000/control-stock/</code>
        </div>

        <form id="cookieForm">
            <div class="form-group">
                <label>Token de Autenticación:</label>
                <select id="token">
                    <option value="123abc456def">123abc456def (Juan Pérez)</option>
                    <option value="test_token">test_token (Admin Test)</option>
                </select>
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

            <button type="submit">🍪 Setear Cookies</button>
        </form>

        <div class="success" id="successMsg">
            ✅ Cookies seteadas correctamente!<br>
            Ahora puedes ir a: <a href="/control-stock/">Control Stock</a>
        </div>
    </div>

    <script>
        document.getElementById('cookieForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const token = document.getElementById('token').value;
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
            
            document.cookie = `authToken=${token}; path=/; max-age=3600`;
            document.cookie = `connection_config=${encodeURIComponent(JSON.stringify(connectionConfig))}; path=/; max-age=3600`;
            
            document.getElementById('successMsg').style.display = 'block';
            
            console.log('✅ Cookies seteadas:');
            console.log('   authToken:', token);
            console.log('   connection_config:', connectionConfig);
        });
    </script>
</body>
</html>'''
    
    return HttpResponse(html)

def controlStock_view(request):
    print("==== CONTROL STOCK VIEW INICIANDO ====")
    
    # 1) Cookies
    token, datos_conexion = obtener_datos_cookies(request)
    
    print(f"🔑 Token obtenido: {token}")
    print(f"📦 Datos conexion: {datos_conexion}")
    
    if not token or not datos_conexion:
        print("❌ REDIRIGIENDO - No hay token o datos")
        return redirect('http://login.cormonsapp.com/login/')

    empresa_nombre = datos_conexion.get('nombre', 'EmpresaDefault')
    
    print(f"✅ Token y datos OK - verificando con VFP...")
    
    # 2) Verificar token
    verificarToken = comando_verificarToken(token, request)
    
    print(f"📡 Respuesta verificarToken: {verificarToken}")

    if not verificarToken["estado"]:
        mensaje = verificarToken.get("mensaje", "Token inválido")
        return renderizar_error(request, mensaje, empresa_nombre)  

    usuario = verificarToken["usuario"]
    nombre = verificarToken["nombre"]

    request.session['usuario'] = usuario
    request.session['nombre'] = nombre

    print(f"✅ Usuario verificado: {usuario}")

    # 3) Consultar pendientes
    respuesta = comando_controlPendientes(token, request, usrActivo=usuario)
    if not respuesta:
        return renderizar_error(request, "Error al obtener stock pendientes", empresa_nombre)

    # 4) Normalizar productos
    pendientes = (
        respuesta.get("pendientes")
        or respuesta.get("PRODUCTOS")
        or respuesta.get("productos")
        or respuesta.get("PENDIENTES")
        or []
    )

    # 5) Render
    return render(request, "app_controlStock/controlStock.html", {
        "pendientes": pendientes,
        "empresa_nombre": empresa_nombre,
        "usuario": usuario,
        "nombre": nombre,
        "deposito": respuesta.get("deposito", ""),
    })


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