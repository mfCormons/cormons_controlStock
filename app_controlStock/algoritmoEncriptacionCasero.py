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
    # Si es bytes, convertir a string primero
    if isinstance(texto_enc, bytes):
        texto_enc = texto_enc.decode('latin-1')

    clave = ord(texto_enc[-1])
    texto_real = texto_enc[:-1]

    resultado = []
    for c in texto_real:
        codigo = (ord(c) - clave) % 256
        resultado.append(chr(codigo))

    return "".join(resultado)

