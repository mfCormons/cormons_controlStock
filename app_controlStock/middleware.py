"""
Middleware para medición de performance
"""
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMiddleware:
    """
    Middleware que mide el tiempo de procesamiento de cada request
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Antes del request
        start_time = time.perf_counter()

        # Procesar request
        response = self.get_response(request)

        # Después del request
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000  # convertir a ms

        # Log solo para paths relevantes (no estáticos)
        if not request.path.startswith('/static/'):
            logger.warning(f"⏱️ [MIDDLEWARE] {request.method} {request.path} - {duration:.2f}ms")
            # Imprimir también a stdout
            print(f"⏱️ [MIDDLEWARE] {request.method} {request.path} - {duration:.2f}ms", flush=True)

        # Agregar header personalizado para debugging en el navegador
        response['X-Response-Time'] = f"{duration:.2f}ms"

        return response
