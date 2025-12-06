#!/usr/bin/env python3
"""
Mock VFP Server - Simula la interfaz Visual FoxPro para testing local
Escucha en localhost:5555 (configurable)
"""
import socket
import json
import threading
import time
from datetime import datetime

# Configuración
HOST = '127.0.0.1'  # localhost
PORT = 5555
BUFFER_SIZE = 2048

# Base de datos mock
TOKENS_VALIDOS = {
    "123abc456def": {
        "usuario": "usuario123",
        "nombre": "Juan Pérez"
    },
    "test_token": {
        "usuario": "admin",
        "nombre": "Admin Test"
    }
}

# Pendientes mock (se reducirán al procesar)
PENDIENTES_MOCK = [
    ["SOL001", "PROD001", "Tornillo 1/4", "2024-12-01"],
    ["SOL002", "PROD002", "Tuerca 1/4", "2024-12-02"],
    ["SOL003", "PROD003", "Arandela M6", "2024-12-03"],
    ["SOL004", "PROD004", "Cable UTP Cat6", "2024-12-04"],
    ["SOL005", "PROD005", "Conector RJ45", "2024-12-05"],
]

# Registro de stocks controlados
STOCKS_CONTROLADOS = []


def encriptar_mock(mensaje):
    """Mock de encriptación - solo devuelve el mensaje"""
    return mensaje


def desencriptar_mock(mensaje):
    """Mock de desencriptación - solo devuelve el mensaje"""
    return mensaje


def procesar_comando(comando_dict):
    """Procesa comandos según el protocolo VFP"""
    comando = comando_dict.get("Comando", "").lower()
    
    print(f"\n📨 Comando recibido: {comando}")
    print(f"   Datos: {json.dumps(comando_dict, indent=2, ensure_ascii=False)}")
    
    # ============ VERIFICAR TOKEN ============
    if comando == "verificartoken":
        token = comando_dict.get("Token", "")
        vista = comando_dict.get("Vista", "")
        
        if token in TOKENS_VALIDOS:
            user_data = TOKENS_VALIDOS[token]
            respuesta = {
                "estado": True,  # Django espera 'estado' minúscula
                "mensaje": "Token válido",
                "usuario": user_data["usuario"],
                "nombre": user_data["nombre"],
                "token": token
            }
            print(f"   ✅ Token válido para: {user_data['nombre']}")
        else:
            respuesta = {
                "estado": False,
                "mensaje": "Token inválido o expirado"
            }
            print(f"   ❌ Token inválido: {token}")
        
        return respuesta
    
    # ============ CONTROL PENDIENTES ============
    elif comando == "controlpendientes":
        token = comando_dict.get("Token", "")
        usr_activo = comando_dict.get("usrActivo", "")
        
        # Validar token
        if token not in TOKENS_VALIDOS:
            return {
                "estado": False,
                "mensaje": "Token inválido"
            }
        
        respuesta = {
            "estado": True,
            "mensaje": "",
            "deposito": "Depósito Central",
            "cod_deposito": "DEP001",
            "pendientes": PENDIENTES_MOCK.copy()  # Copia para no modificar el original
        }
        print(f"   ✅ Devolviendo {len(PENDIENTES_MOCK)} pendientes")
        return respuesta
    
    # ============ STOCK CONTROLADO ============
    elif comando == "stockcontrolado":
        token = comando_dict.get("token", "")
        id_solicitud = comando_dict.get("idSolicitud", "")
        cantidad = comando_dict.get("cantidad", 0)
        usr_activo = comando_dict.get("UsrActivo", "")
        
        # Validar token
        if token not in TOKENS_VALIDOS:
            return {
                "estado": False,
                "mensaje": "Token inválido"
            }
        
        # Buscar y remover la solicitud de pendientes
        solicitud_encontrada = None
        for i, item in enumerate(PENDIENTES_MOCK):
            if item[0] == id_solicitud:
                solicitud_encontrada = PENDIENTES_MOCK.pop(i)
                break
        
        if solicitud_encontrada:
            # Registrar el stock controlado
            registro = {
                "idSolicitud": id_solicitud,
                "codigo": solicitud_encontrada[1],
                "descripcion": solicitud_encontrada[2],
                "cantidad": cantidad,
                "usuario": usr_activo,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            STOCKS_CONTROLADOS.append(registro)
            
            respuesta = {
                "estado": True,
                "mensaje": f"Stock controlado correctamente. Código: {solicitud_encontrada[1]}, Cantidad: {cantidad}"
            }
            print(f"   ✅ Stock controlado: {id_solicitud} - {cantidad} unidades")
            print(f"   📦 Pendientes restantes: {len(PENDIENTES_MOCK)}")
        else:
            respuesta = {
                "estado": False,
                "mensaje": f"Solicitud {id_solicitud} no encontrada"
            }
            print(f"   ❌ Solicitud no encontrada: {id_solicitud}")
        
        return respuesta
    
    # ============ COMANDO DESCONOCIDO ============
    else:
        print(f"   ⚠️  Comando desconocido: {comando}")
        return {
            "estado": False,
            "mensaje": f"Comando '{comando}' no reconocido"
        }


def manejar_cliente(conn, addr):
    """Maneja la conexión de un cliente"""
    print(f"\n🔌 Nueva conexión desde {addr}")
    
    try:
        # Recibir datos
        data = conn.recv(BUFFER_SIZE)
        if not data:
            print(f"   ⚠️  Sin datos recibidos de {addr}")
            return
        
        # Decodificar (mock - asume que viene en latin-1)
        mensaje_recibido = data.decode('latin-1', errors='replace')
        mensaje_desencriptado = desencriptar_mock(mensaje_recibido)
        
        # Parsear JSON
        try:
            comando_dict = json.loads(mensaje_desencriptado)
        except json.JSONDecodeError as e:
            print(f"   ❌ Error parseando JSON: {e}")
            respuesta = {"estado": False, "mensaje": "JSON inválido"}
            respuesta_json = json.dumps(respuesta, ensure_ascii=False)
            conn.sendall(respuesta_json.encode('latin-1', errors='replace'))
            return
        
        # Procesar comando
        respuesta = procesar_comando(comando_dict)
        
        # Enviar respuesta
        respuesta_json = json.dumps(respuesta, ensure_ascii=False)
        respuesta_encriptada = encriptar_mock(respuesta_json)
        conn.sendall(respuesta_encriptada.encode('latin-1', errors='replace'))
        
        print(f"   📤 Respuesta enviada a {addr}")
        
    except Exception as e:
        print(f"   ❌ Error manejando cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"   🔌 Conexión cerrada con {addr}")


def servidor_tcp():
    """Inicia el servidor TCP mock"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        
        print("=" * 60)
        print("🚀 MOCK VFP SERVER INICIADO")
        print("=" * 60)
        print(f"📍 Host: {HOST}")
        print(f"🔌 Puerto: {PORT}")
        print(f"🔑 Tokens válidos:")
        for token, data in TOKENS_VALIDOS.items():
            print(f"   - {token[:20]}... → {data['nombre']}")
        print(f"📦 Pendientes iniciales: {len(PENDIENTES_MOCK)}")
        print("=" * 60)
        print("\n⏳ Esperando conexiones...\n")
        
        try:
            while True:
                conn, addr = s.accept()
                # Manejar cada cliente en un thread separado
                thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n\n🛑 Servidor detenido por usuario")
            print(f"\n📊 RESUMEN DE SESIÓN:")
            print(f"   Stocks controlados: {len(STOCKS_CONTROLADOS)}")
            print(f"   Pendientes restantes: {len(PENDIENTES_MOCK)}")
            if STOCKS_CONTROLADOS:
                print(f"\n📋 Registros de stocks controlados:")
                for reg in STOCKS_CONTROLADOS:
                    print(f"   - {reg['codigo']}: {reg['cantidad']} unidades ({reg['fecha']})")


if __name__ == "__main__":
    servidor_tcp()