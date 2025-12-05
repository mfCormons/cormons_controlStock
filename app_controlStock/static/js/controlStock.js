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

        // Recargar solicitudes al cerrar modal (cumple requisito)
        modalElement.addEventListener('hidden.bs.modal', function() {
            console.log('🔄 Modal cerrado - Recargando solicitudes');
            solicitudSeleccionada = null;
            cargarSolicitudes();
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

    const btnActualizar = document.getElementById('btnActualizar');
    if (btnActualizar) {
        btnActualizar.addEventListener('click', function() {
            console.log('🔁 Botón actualizar presionado');
            cargarSolicitudes();
        });
    }

    // Cargar solicitudes al inicio (cada vez que se recarga la página)
    window.addEventListener('load', function() {
        console.log('🚀 Página cargada - Ejecutando verificación de token y carga de solicitudes');
        // Pequeño timeout para asegurar que otros scripts (si los hay) terminen de inicializar
        setTimeout(() => {
            // Verificar token antes de cargar
            const token = obtenerToken();
            if (!token) {
                console.warn('❌ No se encontró token. Redirigiendo al login.');
                // Ajusta la URL de login según tu app
                setTimeout(() => {
                    window.location.href = '/login/?next=/';
                }, 1000);
                return;
            }
            cargarSolicitudes();
        }, 150);
    });

    // Exponer funciones útiles globalmente si es necesario
    window.cargarSolicitudes = cargarSolicitudes;
    window.abrirModalControl = abrirModalControl;
    window.confirmarControl = confirmarControl;
    window.cerrarSesion = cerrarSesion;

    // ====== Lógica principal ======

    function cargarSolicitudes() {
        console.log('📋 Iniciando carga de solicitudes (pendientes)...');

        const token = obtenerToken();
        if (!token) {
            console.error('❌ No hay token de autenticación');
            mostrarError("Autenticación no encontrada. Redirigiendo al login...");
            setTimeout(() => window.location.href = '/login/', 1500);
            return;
        }

        const container = document.getElementById('solicitudes-container');
        if (!container) {
            console.error('❌ No se encontró el contenedor #solicitudes-container en el DOM');
            return;
        }

        // Mostrar estado de carga
        container.innerHTML = `
            <div class="card-body p-4 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-3 text-muted">Cargando solicitudes...</p>
            </div>
        `;

        // Headers opcionales desde localStorage (según referencia)
        const headers = { 'Content-Type': 'application/json' };
        const empresaIP = localStorage.getItem('empresaIP');
        const empresaPuerto = localStorage.getItem('empresaPuerto');
        const empresaCodigo = localStorage.getItem('empresaCodigo');
        const nombreEmpresa = localStorage.getItem('nombre_empresa');

        if (empresaIP) headers['X-Empresa-IP'] = empresaIP;
        if (empresaPuerto) headers['X-Empresa-Puerto'] = empresaPuerto;
        if (empresaCodigo) headers['X-Empresa-Codigo'] = empresaCodigo;
        if (nombreEmpresa) headers['X-Empresa-Nombre'] = nombreEmpresa;

        // URL de listado (mantengo la ruta del archivo de referencia).
        // Si tu backend expone otro endpoint (p.ej. /api/pendientes/), cámbialo aquí.
        const url = `/control-stock/listar/?token=${encodeURIComponent(token)}`;

        fetch(url, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin' // manda cookies si hacen falta
        })
        .then(response => {
            console.log("📡 Response status:", response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("📋 Respuesta servidor listar:", data);

            // Manejo sesión expirada según referencia
            if (data.estado === false && data.mensaje && data.mensaje.toLowerCase().includes('sesion expirada')) {
                alert('⚠️ Su sesión ha expirado. Será redirigido al login.');
                localStorage.setItem('requiere_credenciales', 'true');
                localStorage.setItem('sesion_activa', 'false');
                window.location.href = '/login/?sesion_expirada=1';
                return;
            }

            if (data.estado === true || data.estado === 'T') {
                // Actualizar header si hay info del servidor
                if (typeof actualizarHeader === 'function') {
                    actualizarHeader(data);
                }
                // Mostrar solicitudes
                if (data.solicitudes && data.solicitudes.length > 0) {
                    mostrarSolicitudes(data.solicitudes);
                } else {
                    mostrarMensaje("✅ No hay solicitudes pendientes", "success");
                }
            } else {
                mostrarError(data.mensaje || 'Error al cargar solicitudes');
            }
        })
        .catch(err => {
            console.error('❌ Error al cargar solicitudes:', err);
            mostrarError('Error al cargar solicitudes. Intente de nuevo.');
        });
    }

    function mostrarSolicitudes(solicitudes) {
        console.log('📋 Mostrando solicitudes:', solicitudes.length);
        const container = document.getElementById('solicitudes-container');
        const template = document.getElementById('solicitudes-template');

        // Si existe template, clonarlo; si no, crear tabla básica
        if (template && template.content) {
            const clone = template.content.cloneNode(true);
            const tbody = clone.querySelector('#solicitudes-tbody');
            if (tbody) {
                solicitudes.forEach(sol => {
                    const tr = document.createElement('tr');
                    tr.className = 'solicitud-row';
                    // Ajusta campos según la estructura que envía tu backend
                    tr.innerHTML = `
                        <td>${sol.fecha_solicitud || ''}</td>
                        <td>${sol.codigo_producto || sol.codigo || ''}</td>
                        <td>${sol.descripcion_producto || sol.descripcion || ''}</td>
                    `;
                    tr.addEventListener('click', () => abrirModalControl(sol));
                    tbody.appendChild(tr);
                });
                container.innerHTML = '';
                container.appendChild(clone);
                return;
            }
        }

        // Fallback: render simple lista
        container.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'table';
        const tbody = document.createElement('tbody');
        solicitudes.forEach(sol => {
            const tr = document.createElement('tr');
            tr.className = 'solicitud-row';
            const fecha = sol.fecha_solicitud || '';
            const codigo = sol.codigo_producto || sol.codigo || '';
            const desc = sol.descripcion_producto || sol.descripcion || '';
            tr.innerHTML = `<td>${fecha}</td><td>${codigo}</td><td>${desc}</td>`;
            tr.addEventListener('click', () => abrirModalControl(sol));
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        container.appendChild(table);
    }

    function abrirModalControl(solicitud) {
        console.log('📋 Abriendo modal para:', solicitud);
        solicitudSeleccionada = solicitud;

        // Llenar modal según IDs que usa la plantilla de referencia
        const modalDescripcion = document.getElementById('modal-descripcion');
        const modalCodigo = document.getElementById('modal-codigo');
        const cantidadInputEl = document.getElementById('cantidad-contada');

        if (modalDescripcion) modalDescripcion.textContent = solicitud.descripcion_producto || solicitud.descripcion || '';
        if (modalCodigo) modalCodigo.textContent = solicitud.codigo_producto || solicitud.codigo || '';
        if (cantidadInputEl) cantidadInputEl.value = '';

        if (modalControl) {
            modalControl.show();
            setTimeout(() => {
                if (cantidadInputEl) cantidadInputEl.focus();
            }, 300);
        } else {
            // Si no hay modal bootstrap, mostrar fallback simple
            alert(`Cargar stock para: ${solicitud.codigo_producto || solicitud.codigo || ''}`);
        }
    }

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

        const mensajeConfirm = `¿Registrar ${cantidadContada} unidades para ${solicitudSeleccionada.codigo_producto || solicitudSeleccionada.codigo || ''}?`;
        if (!confirm(mensajeConfirm)) return;

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
        const empresaIP = localStorage.getItem('empresaIP');
        const empresaPuerto = localStorage.getItem('empresaPuerto');
        const empresaCodigo = localStorage.getItem('empresaCodigo');
        const nombreEmpresa = localStorage.getItem('nombre_empresa');
        if (empresaIP) headers['X-Empresa-IP'] = empresaIP;
        if (empresaPuerto) headers['X-Empresa-Puerto'] = empresaPuerto;
        if (empresaCodigo) headers['X-Empresa-Codigo'] = empresaCodigo;
        if (nombreEmpresa) headers['X-Empresa-Nombre'] = nombreEmpresa;

        // Body según referencia (ajusta keys según tu backend)
        const body = {
            token: token,
            vista: 'control-stock',
            cantidad: cantidadContada,
            codigo_producto: solicitudSeleccionada.codigo_producto || solicitudSeleccionada.codigo || ''
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
                    modalControl.hide(); // El listener 'hidden.bs.modal' recargará solicitudes
                } else {
                    // Si no hay bootstrap, recargar manualmente
                    cargarSolicitudes();
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