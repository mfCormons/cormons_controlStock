import socket
import json
import random

# -------------------------
# ALGORITMO DE ENCRIPTACIÓN
# -------------------------

def encriptar(texto):
    """Encripta sumando una clave random (A-J) al ASCII, modulo 256."""
    clave = random.randint(65, 74)  # A-J
    
    resultado = []
    for c in texto:
        codigo = (ord(c) + clave) % 256
        resultado.append(chr(codigo))
    
    resultado.append(chr(clave))
    return "".join(resultado)

def desencriptar(texto_enc):
    """Desencripta tomando la clave del último caracter."""
    clave = ord(texto_enc[-1])
    texto_real = texto_enc[:-1]
    
    resultado = []
    for c in texto_real:
        codigo = (ord(c) - clave) % 256
        resultado.append(chr(codigo))
    
    return "".join(resultado)

# -------------------------
# DATOS A ENVIAR
# -------------------------

solicitarToken = {
    "Comando": "solicitarToken",  
    "Vista": "LOGIN",
    "Version": 2,
    "Usuario": "a",
    "Clave": "a"
}

verificarToken = {
    "Comando": "verificarToken",  
    "Token": "123",
    "Vista": "LOGIN",
    "version": 2
}

permisosApp = {
    "Comando": "permisosApp",
    "Token": "2512011315080  _7C60SEJQA",
    "Vista": "LANDPAGE",
    "version": 1
}

depositos = {
    "Comando": "depositos",
    "Token": "2512011032360 _7C60MLJ1E",
    "Vista": "CONSULTASTOCK",
    "usrActivo": "a"
}

controlPendientes = {
    "Comando": "controlPendientes",
    "Token": "2512011032360  _7C60MLJ1E",
    "Vista": "CONTROLSTOCK",
    "usrActivo": "a"
}

json_texto = json.dumps(solicitarToken, ensure_ascii=False)
print("\nJSON original:", json_texto)
print("Bytes del JSON:", [ord(c) for c in json_texto[:20]])  # Para debug

mensaje_encriptado = encriptar(json_texto)
clave_usada = ord(mensaje_encriptado[-1])
print(f"\nClave usada: {clave_usada} ('{chr(clave_usada)}')")
print("Encriptado =", repr(mensaje_encriptado))
print("Primeros bytes encriptados:", [ord(c) for c in mensaje_encriptado[:10]])

# -------------------------
# ENVÍO POR TCP
# -------------------------

HOST = "servidorseguro.serinformatica.ar"
PORT = 51122

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        
        print(f"\nConectando a {HOST}:{PORT} ...")
        s.connect((HOST, PORT))
        
        # CRÍTICO: Usar latin-1 en lugar de windows-1252
        # latin-1 mapea directamente 0-255 sin pérdida
        mensaje_bytes = mensaje_encriptado.encode("latin-1")
        print(f"\nBytes a enviar (primeros 10): {mensaje_bytes[:10].hex()}")
        print(f"Valores decimales: {list(mensaje_bytes[:10])}")
        
        s.sendall(mensaje_bytes)
        print("Mensaje enviado correctamente")
        
        # RECIBIR RESPUESTA
        resp = s.recv(2048)
        if resp:
            print(f"\nRespuesta recibida: {len(resp)} bytes")
            print(f"Primeros bytes: {resp[:20].hex()}")
            
            # Decodificar con latin-1 también
            resp_str = resp.decode("latin-1")
            print("Respuesta cruda:", repr(resp_str))
            
            try:
                resp_desencriptada = desencriptar(resp_str)
                print("\nRespuesta desencriptada:", repr(resp_desencriptada))
                
                # Limpiar posibles caracteres extra
                resp_limpia = resp_desencriptada.strip('\x00')
                
                try:
                    resp_json = json.loads(resp_limpia)
                    print("\n✓ JSON recibido:", resp_json)
                except json.JSONDecodeError:
                    # Intentar extraer solo el JSON
                    inicio = resp_limpia.find('{')
                    fin = resp_limpia.rfind('}')
                    if inicio != -1 and fin != -1:
                        json_str = resp_limpia[inicio:fin+1]
                        resp_json = json.loads(json_str)
                        print("\n✓ JSON extraído:", resp_json)
                    else:
                        print("\nLa respuesta NO es JSON válido")
                        
            except Exception as e:
                print(f"\nNo se pudo desencriptar respuesta: {e}")
        else:
            print("\nNo se recibió respuesta")
            
except Exception as e:
    print("\nERROR TCP:", e)
    import traceback
    traceback.print_exc()