"""Error handling middleware."""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and logging errors."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling."""
        start_time = time.time()

        try:
            response = await call_next(request)

            # Log successful requests
            duration = time.time() - start_time
            print(f"✅ {request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            print(f"❌ {request.method} {request.url.path} - ERROR - {duration:.2f}s - {str(e)}")

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred",
                    "timestamp": time.time()
                }
            )
