"""Request/Response logging middleware for FastAPI."""

import time
import uuid
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message

from src.lib.logger import get_logger, set_correlation_id, clear_correlation_id
from src.lib.log_sanitizer import sanitize_headers, sanitize_url, sanitize

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""

    EXCLUDED_PATHS = {'/health', '/docs', '/redoc', '/openapi.json', '/favicon.ico'}
    MAX_BODY_LOG_SIZE = 10000  # Maximum body size to log (10KB)

    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = log_level

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log HTTP requests and responses.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()

        try:
            await self._log_request(request, correlation_id)

            response = await call_next(request)
            response.headers['X-Correlation-ID'] = correlation_id

            process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            await self._log_response(request, response, process_time, correlation_id)

            return response

        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            await self._log_error(request, e, process_time, correlation_id)
            raise
        finally:
            clear_correlation_id()

    async def _log_request(self, request: Request, correlation_id: str):
        """Log incoming request details.

        Args:
            request: HTTP request
            correlation_id: Request correlation ID
        """
        try:
            body = await self._get_request_body(request)

            log_data = {
                'event': 'request_received',
                'correlation_id': correlation_id,
                'method': request.method,
                'path': request.url.path,
                'url': sanitize_url(str(request.url)),
                'headers': sanitize_headers(dict(request.headers)),
                'query_params': dict(request.query_params),
                'client': f"{request.client.host}:{request.client.port}" if request.client else None,
                'user_agent': request.headers.get('User-Agent'),
                'session_id': request.headers.get('X-Session-ID'),
                'channel_type': self._detect_channel_type(request),
            }

            if body and len(body) <= self.MAX_BODY_LOG_SIZE:
                log_data['body'] = sanitize(body)
            elif body:
                log_data['body_truncated'] = True
                log_data['body_size'] = len(body)

            extra = {
                'request_method': request.method,
                'request_path': request.url.path,
                'user_agent': request.headers.get('User-Agent'),
                'session_id': request.headers.get('X-Session-ID'),
                'channel_type': self._detect_channel_type(request),
            }

            logger.info("Request received", extra=extra)
            if self.log_level == "DEBUG":
                logger.debug(f"Request details: {log_data}")

        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def _log_response(self, request: Request, response: Response,
                           process_time: float, correlation_id: str):
        """Log response details.

        Args:
            request: Original HTTP request
            response: HTTP response
            process_time: Request processing time in milliseconds
            correlation_id: Request correlation ID
        """
        try:
            log_data = {
                'event': 'response_sent',
                'correlation_id': correlation_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'process_time_ms': round(process_time, 2),
                'headers': sanitize_headers(dict(response.headers)),
            }

            extra = {
                'request_method': request.method,
                'request_path': request.url.path,
                'response_status': response.status_code,
                'response_time_ms': round(process_time, 2),
                'channel_type': self._detect_channel_type(request),
            }

            if process_time > 5000:  # Log warning for slow responses (>5s)
                logger.warning(f"Slow response: {process_time:.2f}ms", extra=extra)
            else:
                logger.info("Response sent", extra=extra)

            if self.log_level == "DEBUG":
                logger.debug(f"Response details: {log_data}")

        except Exception as e:
            logger.error(f"Error logging response: {e}")

    async def _log_error(self, request: Request, error: Exception,
                        process_time: float, correlation_id: str):
        """Log error details.

        Args:
            request: HTTP request that caused the error
            error: Exception that occurred
            process_time: Processing time before error
            correlation_id: Request correlation ID
        """
        try:
            extra = {
                'request_method': request.method,
                'request_path': request.url.path,
                'response_time_ms': round(process_time, 2),
                'channel_type': self._detect_channel_type(request),
            }

            logger.error(
                f"Request failed: {str(error)}",
                exc_info=True,
                extra=extra
            )

        except Exception as e:
            logger.error(f"Error logging error: {e}")

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely get request body for logging.

        Args:
            request: HTTP request

        Returns:
            Request body as string or None
        """
        try:
            body_bytes = await request.body()
            request._body = body_bytes  # Cache for subsequent middleware
            if body_bytes:
                return body_bytes.decode('utf-8', errors='ignore')
        except Exception:
            pass
        return None

    def _detect_channel_type(self, request: Request) -> str:
        """Detect the channel type from the request.

        Args:
            request: HTTP request

        Returns:
            Channel type (voice, chat, or api)
        """
        path = request.url.path
        if '/voice/' in path or '/twilio/' in path:
            return 'voice'
        elif '/chat/' in path or '/messages' in path:
            return 'chat'
        elif '/sessions' in path:
            session_type = request.headers.get('X-Channel-Type', 'api')
            return session_type
        return 'api'


class APICallLogger:
    """Logger for external API calls."""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def log_api_request(self, api_name: str, method: str, url: str,
                             headers: Optional[dict] = None, body: Optional[dict] = None):
        """Log external API request.

        Args:
            api_name: Name of the external API (e.g., 'EFL_TERMINAL', 'CMA_CGM')
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
        """
        extra = {
            'external_api': api_name,
            'request_method': method,
        }

        log_data = {
            'event': 'external_api_request',
            'api': api_name,
            'method': method,
            'url': sanitize_url(url),
        }

        if headers:
            log_data['headers'] = sanitize_headers(headers)
        if body:
            log_data['body'] = sanitize(body)

        self.logger.info(f"External API request to {api_name}", extra=extra)
        if self.logger.level <= 10:  # DEBUG
            self.logger.debug(f"API request details: {log_data}")

    async def log_api_response(self, api_name: str, status_code: int,
                              response_time: float, body: Optional[dict] = None,
                              error: Optional[str] = None,
                              circuit_breaker_status: Optional[str] = None):
        """Log external API response.

        Args:
            api_name: Name of the external API
            status_code: HTTP status code
            response_time: Response time in milliseconds
            body: Response body
            error: Error message if any
            circuit_breaker_status: Current circuit breaker status
        """
        extra = {
            'external_api': api_name,
            'response_status': status_code,
            'response_time_ms': round(response_time, 2),
        }

        if circuit_breaker_status:
            extra['circuit_breaker_status'] = circuit_breaker_status

        if error:
            self.logger.error(f"External API error from {api_name}: {error}", extra=extra)
        elif status_code >= 400:
            self.logger.warning(f"External API error response from {api_name}", extra=extra)
        else:
            self.logger.info(f"External API response from {api_name}", extra=extra)

        if self.logger.level <= 10 and body:  # DEBUG
            self.logger.debug(f"API response body: {sanitize(body)}")


api_logger = APICallLogger()