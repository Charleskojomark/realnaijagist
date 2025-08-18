"""
Custom middleware for RealNaijaGist
"""
import logging
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log request information and timing"""
    
    def process_request(self, request):
        """Log request start time"""
        request.start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path}")
    
    def process_response(self, request, response):
        """Log request completion time and status"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Request completed: {request.method} {request.path} - {response.status_code} ({duration:.2f}s)")
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with request context"""
        logger.error(f"Exception in {request.method} {request.path}: {str(exception)}", exc_info=True)
        return None


class APIErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware to handle API errors gracefully"""
    
    def process_exception(self, request, exception):
        """Handle exceptions for API requests"""
        # Check if this is an API request
        if request.path.startswith('/api/') or request.path.startswith('/health/'):
            return JsonResponse({
                'error': str(exception),
                'status': 'error'
            }, status=500)
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers"""
    
    def process_response(self, request, response):
        """Add security headers to response"""
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add custom headers
        response['X-Powered-By'] = 'RealNaijaGist'
        
        return response
