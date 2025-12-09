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
            console.log('🔄 Modal cerrado - Actualizando pendientes');
            solicitudSeleccionada = null;
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
    function mostrarAlerta(mensaje, tipo = 'info') {
        const header = document.getElementById('modal-alerta-header');
        const titulo = document.getElementById('modal-alerta-titulo');
        const icono = document.getElementById('modal-alerta-icono');
        const mensajeEl = document.getElementById('modal-alerta-mensaje');
        const btnClose = header ? header.querySelector('.btn-close') : null;
        
        // Configurar colores según tipo
        const configs = {
            'error': {
                headerClass: 'bg-danger text-white',
                titulo: 'Error',
                icono: 'fa-times-circle text-danger'
            },
            'warning': {
                headerClass: 'bg-warning text-dark',
                titulo: 'Advertencia',
                icono: 'fa-exclamation-triangle text-warning'
            },
            'success': {
                headerClass: 'bg-success text-white',
                titulo: 'Éxito',
                icono: 'fa-check-circle text-success'
            },
            'info': {
                headerClass: 'bg-primary text-white',
                titulo: 'Información',
                icono: 'fa-info-circle text-primary'
            }
        };
        
        const config = configs[tipo] || configs.info;
        
        if (header) {
            header.className = `modal-header ${config.headerClass}`;
        }
        if (titulo) {
            titulo.innerHTML = `<i class="fas ${config.icono.split(' ')[0]} me-2"></i>${config.titulo}`;
        }
        if (icono) {
            icono.className = `fas ${config.icono}`;
            icono.style.fontSize = '3rem';
        }
        if (mensajeEl) {
            mensajeEl.textContent = mensaje;
        }
        if (btnClose) {
            btnClose.className = config.headerClass.includes('text-white') ? 'btn-close btn-close-white' : 'btn-close';
        }
        
        if (modalAlerta) {
            modalAlerta.show();
        } else {
            // Fallback
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
        const mensajeConfirm = `¿Está seguro que desea registrar ${cantidadContada} unidades para el código ${solicitudSeleccionada.codigo || solicitudSeleccionada.codigo_producto || ''}?`;
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
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp.json();
        })
        .then(data => {
            console.log('📡 Respuesta registrar:', data);
            
            if (data.estado === true || data.estado === 'T') {
                if (modalControl) {
                    modalControl.hide();
                }
                mostrarAlerta(data.mensaje || 'Control registrado correctamente', 'success');
                solicitudSeleccionada = null;
            } else {
                mostrarAlerta(data.mensaje || 'Error al registrar control', 'error');
                if (btnConfirmar) {
                    btnConfirmar.disabled = false;
                    btnConfirmar.innerHTML = textoOriginal;
                }
            }
        })
        .catch(err => {
            console.error('❌ Error registrar control:', err);
            mostrarAlerta('Error al registrar control. Intente nuevamente.', 'error');
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

    // Exponer funciones globales
    window.abrirModalControl = abrirModalControl;
    window.confirmarControl = confirmarControl;
    window.cerrarSesion = cerrarSesion;
    window.confirmarLogout = confirmarLogout;
    window.ejecutarRegistro = ejecutarRegistro;
    window.mostrarError = mostrarError;

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
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
        return resp.json();
    })
    .then(data => {
        console.log('📡 Pendientes actualizados:', data);
        
        if (data.error) {
            mostrarError(data.error);
            return;
        }
        
        renderizarPendientes(data.pendientes || []);
    })
    .catch(err => {
        console.error('❌ Error al actualizar pendientes:', err);
        mostrarError('Error al actualizar pendientes. Intente nuevamente.');
    })
    .finally(() => {
        if (btnActualizar) {
            btnActualizar.disabled = false;
            btnActualizar.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Actualizar';
        }
    });
}

function renderizarPendientes(pendientes) {
    const container = document.getElementById('solicitudes-container');
    if (!container) return;
    
    if (!pendientes || pendientes.length === 0) {
        container.innerHTML = `
            <div class="card-body p-4 text-center">
                <div class="alert alert-info mb-0">No hay solicitudes pendientes</div>
            </div>
        `;
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