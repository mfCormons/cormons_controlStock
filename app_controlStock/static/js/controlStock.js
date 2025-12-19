// controlStock.js
// Versión adaptada desde controlStockReferencia.js para el proyecto cormons_controlStock
(function() {
    console.log("🔐 INICIANDO CONTROL STOCK JS (adaptado)");

    // Variables/elementos principales
    let solicitudSeleccionada = null;
    let modalControl = null;
    let modalLogout = null;
    let modalConfirmarRegistro = null;
    let modalAlerta = null;
    let errorAutenticacion = false; // Flag para evitar actualizar pendientes tras error 401

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

        // Actualizar pendientes al cerrar modal
        modalElement.addEventListener('hidden.bs.modal', function() {
            console.log('🔄 Modal cerrado');
            solicitudSeleccionada = null;

            // Si hubo error de autenticación, NO actualizar pendientes
            // (la sesión ya fue limpiada y se va a redirigir al login)
            if (errorAutenticacion) {
                console.log('⚠️ Error de autenticación detectado - NO actualizando pendientes');
                errorAutenticacion = false; // Resetear flag
                return;
            }

            console.log('✅ Actualizando pendientes');
            // Restaurar estado del botón Confirmar si quedó deshabilitado
            try {
                const btn = modalElement.querySelector('.btn-success');
                if (btn && btn.dataset && btn.dataset.origHtml) {
                    btn.disabled = false;
                    btn.innerHTML = btn.dataset.origHtml;
                    delete btn.dataset.origHtml;
                }
            } catch (e) {
                console.warn('No se pudo restaurar el botón confirmar del modal', e);
            }
            actualizarPendientes();
        });
    }

    // Inicializar modal de confirmación
    const modalConfirmarElement = document.getElementById('modalConfirmarRegistro');
    if (modalConfirmarElement && window.bootstrap) {
        modalConfirmarRegistro = new bootstrap.Modal(modalConfirmarElement);
    }

    const modalLogoutElement = document.getElementById('modalLogout');
    if (modalLogoutElement && window.bootstrap) {
        modalLogout = new bootstrap.Modal(modalLogoutElement);
    }

    // Inicializar modal de alerta
    const modalAlertaElement = document.getElementById('modalAlerta');
    if (modalAlertaElement && window.bootstrap) {
        modalAlerta = new bootstrap.Modal(modalAlertaElement);
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

    // Función helper para mostrar alertas
    // - Para 'success' muestra notificaciones no bloqueantes (toasts)
    // - Para 'info-modal' muestra modal bloqueante informativo (mensajes de VFP)
    // - Para 'error' y 'warning' mantiene el modal bloqueante existente
    function mostrarAlerta(mensaje, tipo = 'info') {
        const useToast = (tipo === 'success');

        if (useToast) {
            // Crear contenedor de toasts si no existe
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.style.position = 'fixed';
                container.style.top = '1rem';
                container.style.right = '1rem';
                container.style.zIndex = 11000;
                container.style.display = 'flex';
                container.style.flexDirection = 'column';
                container.style.gap = '0.5rem';
                document.body.appendChild(container);
            }

            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${tipo === 'success' ? 'success' : 'info'} shadow-sm`;
            alertDiv.style.minWidth = '240px';
            alertDiv.style.maxWidth = '360px';
            alertDiv.style.borderRadius = '6px';
            alertDiv.style.boxShadow = '0 2px 8px rgba(0,0,0,0.12)';
            alertDiv.innerHTML = `
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="flex:1;font-size:0.95rem;">${mensaje}</div>
                    <button type="button" aria-label="cerrar" style="background:none;border:none;font-size:1rem;" class="btn-close"></button>
                </div>
            `;

            const btnClose = alertDiv.querySelector('.btn-close');
            btnClose.addEventListener('click', () => {
                if (alertDiv && alertDiv.parentNode) alertDiv.parentNode.removeChild(alertDiv);
            });

            container.appendChild(alertDiv);

            // Auto-dismiss
            const timeout = tipo === 'success' ? 3000 : 5000;
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode) alertDiv.parentNode.removeChild(alertDiv);
            }, timeout);
            return;
        }

        // Para errores/advertencias usar modal existente
        const header = document.getElementById('modal-alerta-header');
        const titulo = document.getElementById('modal-alerta-titulo');
        const icono = document.getElementById('modal-alerta-icono');
        const mensajeEl = document.getElementById('modal-alerta-mensaje');
        const btnClose = header ? header.querySelector('.btn-close') : null;

        const configs = {
            'error': { headerClass: 'bg-danger text-white', titulo: 'Error', icono: 'fa-times-circle text-danger' },
            'warning': { headerClass: 'bg-warning text-dark', titulo: 'Advertencia', icono: 'fa-exclamation-triangle text-warning' },
            'info-modal': { headerClass: 'bg-info text-white', titulo: 'Información', icono: 'fa-info-circle text-info' }
        };

        const config = configs[tipo] || configs['info-modal'];
        if (header) header.className = `modal-header ${config.headerClass}`;
        if (titulo) titulo.innerHTML = `<i class="fas ${config.icono.split(' ')[0]} me-2"></i>${config.titulo}`;
        if (icono) { icono.className = `fas ${config.icono}`; icono.style.fontSize = '3rem'; }
        if (mensajeEl) mensajeEl.textContent = mensaje;
        if (btnClose) btnClose.className = config.headerClass.includes('text-white') ? 'btn-close btn-close-white' : 'btn-close';

        console.log('🔔 mostrarAlerta - tipo:', tipo, 'modalAlerta:', modalAlerta);
        if (modalAlerta) {
            try {
                modalAlerta.show();
                console.log('✅ Modal mostrado correctamente');
            } catch (err) {
                console.error('❌ Error al mostrar modal:', err);
                alert(mensaje);
            }
        } else {
            console.warn('⚠️ modalAlerta no está inicializado');
            alert(mensaje);
        }
    }

    function abrirModalControl(solicitud) {
        console.log('📋 Abriendo modal para:', solicitud);

        solicitudSeleccionada = solicitud || {};

        const modalDescripcion = document.getElementById('modal-descripcion');
        const modalCodigo = document.getElementById('modal-codigo');
        const cantidadInputEl = document.getElementById('cantidad-contada');

        const desc = solicitud.descripcion_producto || solicitud.descripcion || solicitud.desc || '';
        const cod = solicitud.codigo_producto || solicitud.codigo || solicitud.cod || '';

        if (modalDescripcion) modalDescripcion.textContent = desc;
        if (modalCodigo) modalCodigo.textContent = cod;
        if (cantidadInputEl) cantidadInputEl.value = '';

        if (modalControl) {
            modalControl.show();
            setTimeout(() => { if (cantidadInputEl) cantidadInputEl.focus(); }, 300);
        } else {
            mostrarAlerta(`Cargar stock para: ${cod}`, 'info');
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
            mostrarAlerta('No hay solicitud seleccionada', 'warning');
            return;
        }

        const cantidadEl = document.getElementById('cantidad-contada');
        const cantidadContada = cantidadEl ? cantidadEl.value.trim() : '';

        if (!cantidadContada) {
            mostrarAlerta('Por favor, ingrese la cantidad contada', 'warning');
            if (cantidadEl) cantidadEl.focus();
            return;
        }
        if (isNaN(cantidadContada) || parseFloat(cantidadContada) < 0) {
            mostrarAlerta('Ingrese un número válido mayor o igual a 0', 'error');
            if (cantidadEl) cantidadEl.focus();
            return;
        }

        const token = obtenerToken();
        let tokenLimpio = token;
        if (tokenLimpio) {
            tokenLimpio = tokenLimpio.replace(/^["']+|["']+$/g, '');
            tokenLimpio = tokenLimpio.replace(/\\/g, '');
            tokenLimpio = tokenLimpio.trim();
        }

        if (!tokenLimpio) {
            mostrarAlerta('No hay token de autenticación', 'error');
            return;
        }

        // Mostrar modal de confirmación
        const codigo = solicitudSeleccionada.codigo || solicitudSeleccionada.codigo_producto || '';
        const descripcion = solicitudSeleccionada.descripcion || '';

        // Obtener depósito del header
        const depositoEl = document.getElementById('deposito-info') || document.getElementById('deposito-info-desktop');
        const deposito = depositoEl ? depositoEl.textContent.trim() : '';

        const mensajeConfirm = `¿Está seguro que desea registrar ${cantidadContada} unidades?\n\n${descripcion}${codigo ? ' (' + codigo + ')' : ''}${deposito ? '\nDepósito: ' + deposito : ''}`;
        document.getElementById('confirmar-mensaje').textContent = mensajeConfirm;
        
        if (modalConfirmarRegistro) {
            modalConfirmarRegistro.show();
        } else {
            ejecutarRegistro();
        }
    }

    function ejecutarRegistro() {
        if (modalConfirmarRegistro) {
            modalConfirmarRegistro.hide();
        }

        const cantidadEl = document.getElementById('cantidad-contada');
        const cantidadContada = cantidadEl ? cantidadEl.value.trim() : '';
        
        const token = obtenerToken();
        let tokenLimpio = token;
        if (tokenLimpio) {
            tokenLimpio = tokenLimpio.replace(/^["']+|["']+$/g, '');
            tokenLimpio = tokenLimpio.replace(/\\/g, '');
            tokenLimpio = tokenLimpio.trim();
        }

        const btnConfirmar = modalElement ? modalElement.querySelector('.btn-success') : null;
        let textoOriginal = null;
        if (btnConfirmar) {
            textoOriginal = btnConfirmar.innerHTML;
            // Guardar HTML original en data-attribute para poder restaurarlo si el modal se cierra
            try { btnConfirmar.dataset.origHtml = textoOriginal; } catch (e) { /* ignore */ }
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
        }

        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
        };

        const body = {
            token: tokenLimpio,
            idSolicitud: solicitudSeleccionada.idSolicitud || solicitudSeleccionada[0] || '',
            cantidad: cantidadContada
        };

        fetch('/registrar/', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body),
            credentials: 'same-origin'
        })
        .then(resp => {
            // Si es 401, parsear el JSON para obtener el redirect y mensaje de VFP
            if (resp.status === 401) {
                return resp.json().then(data => {
                    console.log('🚫 Error 401 - Usuario deshabilitado o sesión inválida');
                    const redirectUrl = data.redirect || 'https://login.cormons.app/login/?logout=1';
                    // SIEMPRE usar el mensaje de VFP (data.error)
                    const mensaje = data.error || data.mensaje || 'Error de autenticación';

                    // Marcar que hubo error de autenticación para evitar actualizar pendientes
                    errorAutenticacion = true;

                    // Cerrar modal de control si está abierto
                    if (modalControl) {
                        modalControl.hide();
                    }

                    // Mostrar modal de error bloqueante (sin countdown)
                    window.mostrarErrorConRedirect(mensaje, redirectUrl);
                    throw new Error('Sesión inválida');
                });
            }
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp.json();
        })
        .then(data => {
            console.log('📡 Respuesta registrar:', data);

            if (data.estado === true || data.estado === 'T') {
                if (modalControl) {
                    modalControl.hide();
                }
                // Solo mostrar modal si VFP envió un mensaje
                if (data.mensaje && data.mensaje.trim() !== '') {
                    mostrarAlerta(data.mensaje, 'info-modal');
                }
                // Restaurar botón confirmar si quedó con spinner
                if (btnConfirmar) {
                    try {
                        btnConfirmar.disabled = false;
                        btnConfirmar.innerHTML = textoOriginal || btnConfirmar.dataset.origHtml || '<i class="fas fa-check me-1"></i>Confirmar';
                        delete btnConfirmar.dataset.origHtml;
                    } catch (e) { console.warn('No se pudo restaurar btnConfirmar tras éxito', e); }
                }
                solicitudSeleccionada = null;
            } else {
                // SIEMPRE usar mensaje de VFP si existe (incluso si es vacío)
                const mensaje = data.mensaje !== undefined && data.mensaje !== null ? data.mensaje : 'Error en la operación';
                mostrarAlerta(mensaje, 'error');
                if (btnConfirmar) {
                    btnConfirmar.disabled = false;
                    btnConfirmar.innerHTML = textoOriginal;
                }
            }
        })
        .catch(err => {
            console.error('❌ Error registrar control:', err);
            // No mostrar alerta si ya estamos redirigiendo
            if (err.message !== 'Sesión inválida') {
                // Error de red o servidor - mostrar error genérico
                mostrarAlerta('Error de comunicación. Intente nuevamente.', 'error');
            }
            if (btnConfirmar && err.message !== 'Sesión inválida') {
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
        if (modalLogout) {
            modalLogout.show();
        } else {
            if (confirm('¿Está seguro que desea cerrar sesión?')) {
                window.location.href = '/logout/';
            }
        }
    }

    function confirmarLogout() {
        if (modalLogout) {
            modalLogout.hide();
        }
        window.location.href = '/logout/';
    }

    // Función para mostrar modal de error con redirección (bloquea interacción)
    // SIN countdown - usuario debe hacer click para continuar
    function mostrarErrorConRedirect(mensaje, redirectUrl) {
        const modalElement = document.getElementById('modalErrorRedirect');
        const mensajeEl = document.getElementById('modal-error-mensaje');
        const countdownContainer = document.getElementById('modal-countdown-container');
        const btnRedirect = document.getElementById('btn-redirect-now');

        if (!modalElement || !window.bootstrap) {
            // Fallback si no existe el modal
            alert(mensaje);
            window.location.href = redirectUrl;
            return;
        }

        // Configurar mensaje (siempre usar el mensaje de VFP)
        if (mensajeEl) mensajeEl.textContent = mensaje;

        // Ocultar el countdown (no se usa más - usuario debe hacer click)
        if (countdownContainer) {
            countdownContainer.style.display = 'none';
        }

        // Crear modal con opciones de bloqueo
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });

        // Botón para ir al login (usuario debe hacer click)
        if (btnRedirect) {
            btnRedirect.onclick = function() {
                window.location.href = redirectUrl;
            };
        }

        modal.show();
    }

    // Exponer funciones globales
    window.abrirModalControl = abrirModalControl;
    window.confirmarControl = confirmarControl;
    window.cerrarSesion = cerrarSesion;
    window.confirmarLogout = confirmarLogout;
    window.ejecutarRegistro = ejecutarRegistro;
    window.mostrarError = mostrarError;
    window.mostrarErrorConRedirect = mostrarErrorConRedirect;
    window.mostrarAlerta = mostrarAlerta;

    console.log('✅ controlStock.js inicializado (adaptado)');
})();

function actualizarPendientes() {
    console.log('🔄 Actualizando pendientes...');
    
    const btnActualizar = document.getElementById('btn-actualizar');
    const container = document.getElementById('solicitudes-container');
    
    if (btnActualizar) {
        btnActualizar.disabled = true;
        btnActualizar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Actualizando...';
    }
    
    if (container) {
        container.innerHTML = `
            <div class="card-body p-4 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 mb-0">Actualizando pendientes...</p>
            </div>
        `;
    }
    
    fetch('/pendientes/', {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(resp => {
        // Si es 401, parsear el JSON para obtener el redirect y mensaje de VFP
        if (resp.status === 401) {
            return resp.json().then(data => {
                console.log('🚫 Sesión inválida - mostrando modal de error con mensaje de VFP');
                const redirectUrl = data.redirect || 'https://login.cormons.app/login/?logout=1';
                // SIEMPRE usar el mensaje de VFP (data.error)
                const mensaje = data.error || data.mensaje || 'Error de autenticación';

                // Mostrar modal de error bloqueante (sin countdown)
                window.mostrarErrorConRedirect(mensaje, redirectUrl);
                throw new Error('Sesión inválida');
            });
        }
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
        return resp.json();
    })
    .then(data => {
        console.log('📡 Pendientes actualizados:', data);
        console.log('📦 DEBUG: data.deposito =', data.deposito);
        console.log('📦 DEBUG: typeof data.deposito =', typeof data.deposito);

        // Si VFP devolvió error, mostrarlo
        if (data.error) {
            // Usar mensaje de VFP
            mostrarError(data.error);
            return;
        }

        // Actualizar depósito si viene en la respuesta
        console.log('📦 Buscando elementos de depósito...');
        const depositoElMobile = document.getElementById('deposito-info');
        const depositoElDesktop = document.getElementById('deposito-info-desktop');
        console.log('📦 Elementos encontrados:', { mobile: depositoElMobile, desktop: depositoElDesktop });

        if (data.deposito) {
            // Actualizar AMBOS elementos (móvil y desktop) para que funcione en todas las pantallas
            if (depositoElMobile) {
                depositoElMobile.textContent = data.deposito;
                console.log('✅ Depósito móvil actualizado:', data.deposito);
            }
            if (depositoElDesktop) {
                depositoElDesktop.textContent = data.deposito;
                console.log('✅ Depósito desktop actualizado:', data.deposito);
            }
            if (!depositoElMobile && !depositoElDesktop) {
                console.warn('⚠️ No se encontró ningún elemento de depósito');
            }
        } else {
            console.warn('⚠️ data.deposito está vacío o undefined');
        }

        renderizarPendientes(data.pendientes || [], data.mensaje);
    })
    .catch(err => {
        console.error('❌ Error al actualizar pendientes:', err);
        // No mostrar error si ya estamos redirigiendo
        if (err.message !== 'Sesión inválida') {
            mostrarError('Error de comunicación. Intente nuevamente.');
        }
    })
    .finally(() => {
        if (btnActualizar) {
            btnActualizar.disabled = false;
            btnActualizar.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Actualizar';
        }
    });
}

function renderizarPendientes(pendientes, mensajeVFP) {
    const container = document.getElementById('solicitudes-container');
    if (!container) return;

    // Si VFP envió un mensaje, mostrarlo como modal bloqueante
    if (mensajeVFP) {
        mostrarAlerta(mensajeVFP, 'info-modal');
    }

    if (!pendientes || pendientes.length === 0) {
        // Mostrar mensaje simple en el área (sin el mensaje de VFP, ya se mostró en modal)
        const mensajeArea = mensajeVFP ? '' : 'No hay solicitudes pendientes';
        if (mensajeArea) {
            container.innerHTML = `
                <div class="card-body p-4 text-center">
                    <div class="alert alert-info mb-0">${mensajeArea}</div>
                </div>
            `;
        } else {
            // Si hay mensaje de VFP, dejar el área vacía o con un placeholder
            container.innerHTML = `
                <div class="card-body p-4 text-center">
                    <div class="alert alert-info mb-0">No hay solicitudes pendientes</div>
                </div>
            `;
        }
        return;
    }
    
    let html = `
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th class="fw-semibold">Fecha Solicitud</th>
                            <th class="fw-semibold">Código</th>
                            <th class="fw-semibold">Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    pendientes.forEach(item => {
        const id = Array.isArray(item) ? item[0] : (item.idsolicitud || item.idSolicitud || '');
        const codigo = Array.isArray(item) ? item[1] : (item.codigo || '');
        const descripcion = Array.isArray(item) ? item[2] : (item.descripcion || '');
        const fecha = Array.isArray(item) ? item[3] : (item.fecha || '');
        
        html += `
            <tr class="solicitud-row"
                data-id="${id}"
                data-cod="${codigo}"
                data-desc="${descripcion}"
                data-fecha="${fecha}"
                onclick="abrirModalControlFromRow(this)">
                <td>${fecha}</td>
                <td>${codigo}</td>
                <td>${descripcion}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

window.actualizarPendientes = actualizarPendientes;