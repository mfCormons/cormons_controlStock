// controlStock.js
// Versión adaptada desde controlStockReferencia.js para el proyecto cormons_controlStock
(function() {
    console.log("🔐 INICIANDO CONTROL STOCK JS (adaptado)");

    // Variables/elementos principales
    let solicitudSeleccionada = null;
    let modalControl = null;

    // Helpers para cookies
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Intentar obtener token desde varias fuentes (priorizando la cookie usada en backend)
    function obtenerToken() {
        // Backend usa 'authToken' en utils.obtener_datos_cookies
        return getCookie('authToken') || getCookie('token') || localStorage.getItem('authToken') || null;
    }

    // Inicializar referencias DOM (según el HTML de referencia)
    const modalElement = document.getElementById('modalControl');
    if (modalElement && window.bootstrap) {
        modalControl = new bootstrap.Modal(modalElement);

        // Recargar la página al cerrar modal (server re-render traerá nuevos pendientes)
        modalElement.addEventListener('hidden.bs.modal', function() {
            console.log('🔄 Modal cerrado - Recargando página');
            solicitudSeleccionada = null;
            window.location.reload();
        });
    }

    const cantidadInput = document.getElementById('cantidad-contada');
    if (cantidadInput) {
        cantidadInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                confirmarControl();
            }
        });
    }

    // El botón "Actualizar" en la plantilla hace un reload simple (onclick="location.reload()")

    // Exponer funciones globales necesarias
    window.abrirModalControl = abrirModalControl;
    window.confirmarControl = confirmarControl;
    window.cerrarSesion = cerrarSesion;

    // ====== Lógica principal (simplificada para server-render) ======

    function mostrarSolicitudes(solicitudes) {
        // En la opción A (server-render) esta función no se usa; queda para compatibilidad.
        console.log('mostrarSolicitudes llamado (no usado en server-render)');
    }

    function abrirModalControl(solicitud) {
        console.log('📋 Abriendo modal para:', solicitud);

        // Acepta como 'solicitud' un objeto con keys: idSolicitud, codigo, descripcion, fecha
        solicitudSeleccionada = solicitud || {};

        const modalDescripcion = document.getElementById('modal-descripcion');
        const modalCodigo = document.getElementById('modal-codigo');
        const cantidadInputEl = document.getElementById('cantidad-contada');

        const desc = solicitud.descripcion_producto || solicitud.descripcion || solicitud.desc || solicitud.descripcion_producto || solicitud.descripcion || solicitud.description || '';
        const cod = solicitud.codigo_producto || solicitud.codigo || solicitud.cod || '';

        if (modalDescripcion) modalDescripcion.textContent = desc;
        if (modalCodigo) modalCodigo.textContent = cod;
        if (cantidadInputEl) cantidadInputEl.value = '';

        if (modalControl) {
            modalControl.show();
            setTimeout(() => { if (cantidadInputEl) cantidadInputEl.focus(); }, 300);
        } else {
            alert(`Cargar stock para: ${cod}`);
        }
    }

    // Helper: abrir modal desde una fila que contiene data-* attributes
    window.abrirModalControlFromRow = function(el) {
        if (!el || !el.dataset) return;
        const obj = {
            idSolicitud: el.dataset.id || el.getAttribute('data-id') || '',
            codigo: el.dataset.cod || el.getAttribute('data-cod') || '',
            descripcion: el.dataset.desc || el.getAttribute('data-desc') || '',
            fecha: el.dataset.fecha || el.getAttribute('data-fecha') || ''
        };
        abrirModalControl(obj);
    };

    function confirmarControl() {
        if (!solicitudSeleccionada) {
            alert('No hay solicitud seleccionada');
            return;
        }

        const cantidadEl = document.getElementById('cantidad-contada');
        const cantidadContada = cantidadEl ? cantidadEl.value.trim() : '';

        if (!cantidadContada) {
            alert('Por favor, ingrese la cantidad contada');
            if (cantidadEl) cantidadEl.focus();
            return;
        }
        if (isNaN(cantidadContada) || parseFloat(cantidadContada) < 0) {
            alert('Ingrese un número válido mayor o igual a 0');
            if (cantidadEl) cantidadEl.focus();
            return;
        }

        const token = obtenerToken();
        if (!token) {
            alert('No hay token de autenticación');
            return;
        }

        // Confirmación extra antes de enviar
        const mensajeConfirm = `¿Está seguro que desea registrar ${cantidadContada} unidades para el código ${solicitudSeleccionada.codigo || solicitudSeleccionada.codigo_producto || ''}?`;
        if (!window.confirm(mensajeConfirm)) return;

        // Botón confirmar en modal (si existe)
        const btnConfirmar = modalElement ? modalElement.querySelector('.btn-success') : null;
        let textoOriginal = null;
        if (btnConfirmar) {
            textoOriginal = btnConfirmar.innerHTML;
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
        }

        // Headers (incluimos CSRF si fuera necesario)
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
        };

        // Body según referencia (ajusta keys según tu backend)
        const body = {
            token: token,
            idSolicitud: solicitudSeleccionada.idSolicitud || solicitudSeleccionada[0] || '',
            cantidad: cantidadContada
        };

        fetch('/control-stock/registrar/', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body),
            credentials: 'same-origin'
        })
        .then(resp => {
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp.json();
        })
        .then(data => {
            console.log('📡 Respuesta registrar:', data);
            if (data.estado === false && data.mensaje && data.mensaje.toLowerCase().includes('sesion expirada')) {
                alert('⚠️ Su sesión ha expirado. Será redirigido al login.');
                localStorage.setItem('requiere_credenciales', 'true');
                localStorage.setItem('sesion_activa', 'false');
                window.location.href = '/login/?sesion_expirada=1';
                return;
            }

            if (data.estado === true || data.estado === 'T') {
                if (modalControl) {
                    modalControl.hide(); // El listener 'hidden.bs.modal' recargará la página
                } else {
                    // Si no hay bootstrap, recargar manualmente
                    window.location.reload();
                }
                alert('✅ ' + (data.mensaje || 'Control registrado correctamente'));
                solicitudSeleccionada = null;
            } else {
                alert('❌ ' + (data.mensaje || 'Error al registrar control'));
                if (btnConfirmar) {
                    btnConfirmar.disabled = false;
                    btnConfirmar.innerHTML = textoOriginal;
                }
            }
        })
        .catch(err => {
            console.error('❌ Error registrar control:', err);
            alert('Error al registrar control. Intente nuevamente.');
            if (btnConfirmar) {
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = textoOriginal;
            }
        });
    }

    function mostrarMensaje(mensaje, tipo = "info") {
        const container = document.getElementById('solicitudes-container');
        if (!container) return;
        const colores = {
            'success': 'alert-success',
            'info': 'alert-info',
            'warning': 'alert-warning',
            'error': 'alert-danger'
        };
        const color = colores[tipo] || colores.info;
        container.innerHTML = `
            <div class="card-body p-4">
                <div class="alert ${color} mb-0">${mensaje}</div>
            </div>
        `;
    }

    function mostrarError(mensaje) {
        mostrarMensaje(mensaje, 'error');
    }

    function cerrarSesion() {
        if (confirm('¿Cerrar sesión?')) {
            localStorage.setItem('requiere_credenciales', 'true');
            localStorage.setItem('sesion_activa', 'false');
            window.location.href = '/logout/';
        }
    }

    console.log('✅ controlStock.js inicializado (adaptado)');
})();