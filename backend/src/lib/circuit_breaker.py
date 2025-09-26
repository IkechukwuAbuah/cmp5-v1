"""Circuit breaker implementation for external API calls."""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional
from weakref import WeakKeyDictionary

from src.core.config import settings
from src.lib.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back up


@dataclass
class CircuitBreaker:
    """Circuit breaker for a specific service."""

    name: str
    failure_threshold: int = field(default_factory=lambda: settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD)
    timeout: int = field(default_factory=lambda: settings.CIRCUIT_BREAKER_TIMEOUT)
    expected_exception: Exception = Exception

    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _last_failure_time: Optional[float] = None
    _success_count: int = 0
    _calls: WeakKeyDictionary = field(default_factory=WeakKeyDictionary)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.timeout

    def _can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self._state == CircuitState.CLOSED:
            return True
        elif self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                return True
            return False
        elif self._state == CircuitState.HALF_OPEN:
            return True
        return False

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self._can_execute():
            raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is OPEN")

        try:
            # Record the call
            self._calls[func] = time.time()

            # Execute the function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Success handling
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            # Re-raise unexpected exceptions without affecting circuit breaker
            raise e

    def _on_success(self) -> None:
        """Handle successful call."""
        self._failure_count = 0
        self._success_count += 1

        if self._state == CircuitState.HALF_OPEN and self._success_count >= 1:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._success_count = 0
            logger.info(
                f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {self._state.value}",
                extra={'circuit_breaker_status': self._state.value}
            )

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            old_state = self._state
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self._failure_count} failures",
                extra={'circuit_breaker_status': self._state.value}
            )

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count


class CircuitBreakerManager:
    """Global circuit breaker manager."""

    _breakers: Dict[str, CircuitBreaker] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the circuit breaker manager."""
        if cls._initialized:
            return

        cls._breakers = {
            "efl_terminal": CircuitBreaker("efl_terminal"),
            "cma_cgm": CircuitBreaker("cma_cgm"),
            "openai": CircuitBreaker("openai"),
            "twilio": CircuitBreaker("twilio"),
        }

        cls._initialized = True

    @classmethod
    def get_breaker(cls, name: str) -> CircuitBreaker:
        """Get circuit breaker by name."""
        if not cls._initialized:
            cls.initialize()

        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name)

        return cls._breakers[name]

    @classmethod
    def get_all_breakers(cls) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers."""
        if not cls._initialized:
            cls.initialize()
        return cls._breakers.copy()


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass
