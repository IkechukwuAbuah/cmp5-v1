"""Log sanitization utilities to remove sensitive data."""

import re
from typing import Any, Dict, List, Optional, Set, Union
from copy import deepcopy


class LogSanitizer:
    """Sanitize sensitive data from logs."""

    SENSITIVE_PATTERNS = {
        'api_key': re.compile(r'(api[_\-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]+)["\']?', re.IGNORECASE),
        'token': re.compile(r'(token|jwt|bearer)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]+)["\']?', re.IGNORECASE),
        'password': re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
        'secret': re.compile(r'(secret|private[_\-]?key)["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
        'credit_card': re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(\+\d{1,3}[\s\-]?)?\(?\d{3,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'container_id': re.compile(r'\b[A-Z]{4}\d{7}\b'),  # Container IDs might be sensitive in some contexts
    }

    SENSITIVE_KEYS: Set[str] = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
        'authorization', 'auth', 'cookie', 'session', 'credit_card', 'cc',
        'ssn', 'social_security', 'private_key', 'client_secret', 'refresh_token',
        'access_token', 'id_token', 'bearer', 'jwt', 'x-api-key', 'x-auth-token'
    }

    REDACTED = '***REDACTED***'
    PARTIAL_MASK_CHAR = '*'

    def __init__(self, custom_patterns: Optional[Dict[str, re.Pattern]] = None,
                 custom_keys: Optional[Set[str]] = None):
        """Initialize sanitizer with optional custom patterns and keys.

        Args:
            custom_patterns: Additional regex patterns to sanitize
            custom_keys: Additional keys to sanitize
        """
        self.patterns = self.SENSITIVE_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)

        self.sensitive_keys = self.SENSITIVE_KEYS.copy()
        if custom_keys:
            self.sensitive_keys.update(custom_keys)

    def sanitize_string(self, text: str, partial_mask: bool = False) -> str:
        """Sanitize sensitive data from a string.

        Args:
            text: Text to sanitize
            partial_mask: If True, partially mask values instead of full redaction

        Returns:
            Sanitized text
        """
        if not text:
            return text

        sanitized = text
        for pattern_name, pattern in self.patterns.items():
            if partial_mask and pattern_name in ['email', 'phone', 'container_id']:
                def mask_match(match):
                    full_match = match.group(0)
                    if pattern_name == 'email':
                        parts = full_match.split('@')
                        if len(parts) == 2:
                            masked_user = parts[0][:2] + self.PARTIAL_MASK_CHAR * (len(parts[0]) - 2)
                            return f"{masked_user}@{parts[1]}"
                    elif pattern_name == 'phone':
                        visible_digits = 4
                        if len(full_match) > visible_digits:
                            return self.PARTIAL_MASK_CHAR * (len(full_match) - visible_digits) + full_match[-visible_digits:]
                    elif pattern_name == 'container_id':
                        return full_match[:4] + self.PARTIAL_MASK_CHAR * 7
                    return full_match

                sanitized = pattern.sub(mask_match, sanitized)
            else:
                sanitized = pattern.sub(self.REDACTED, sanitized)

        return sanitized

    def sanitize_dict(self, data: Dict[str, Any], deep_copy: bool = True) -> Dict[str, Any]:
        """Sanitize sensitive data from a dictionary.

        Args:
            data: Dictionary to sanitize
            deep_copy: If True, create a deep copy before sanitizing

        Returns:
            Sanitized dictionary
        """
        if not data:
            return data

        result = deepcopy(data) if deep_copy else data

        for key in list(result.keys()):
            lower_key = key.lower()

            if any(sensitive in lower_key for sensitive in self.sensitive_keys):
                result[key] = self.REDACTED
            elif isinstance(result[key], str):
                result[key] = self.sanitize_string(result[key], partial_mask=True)
            elif isinstance(result[key], dict):
                result[key] = self.sanitize_dict(result[key], deep_copy=False)
            elif isinstance(result[key], list):
                result[key] = self.sanitize_list(result[key], deep_copy=False)

        return result

    def sanitize_list(self, data: List[Any], deep_copy: bool = True) -> List[Any]:
        """Sanitize sensitive data from a list.

        Args:
            data: List to sanitize
            deep_copy: If True, create a deep copy before sanitizing

        Returns:
            Sanitized list
        """
        if not data:
            return data

        result = deepcopy(data) if deep_copy else data

        for i, item in enumerate(result):
            if isinstance(item, str):
                result[i] = self.sanitize_string(item, partial_mask=True)
            elif isinstance(item, dict):
                result[i] = self.sanitize_dict(item, deep_copy=False)
            elif isinstance(item, list):
                result[i] = self.sanitize_list(item, deep_copy=False)

        return result

    def sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize HTTP headers.

        Args:
            headers: Headers dictionary to sanitize

        Returns:
            Sanitized headers
        """
        if not headers:
            return headers

        sanitized = {}
        for key, value in headers.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in ['authorization', 'cookie', 'x-api-key', 'x-auth-token']):
                if value and len(value) > 10:
                    sanitized[key] = value[:6] + '...' + self.REDACTED
                else:
                    sanitized[key] = self.REDACTED
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_url(self, url: str) -> str:
        """Sanitize sensitive data from URLs.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        if not url:
            return url

        patterns = [
            (r'([?&])(api_key|token|auth|key)=([^&]+)', r'\1\2=' + self.REDACTED),
            (r'(https?://[^:]+:)([^@]+)(@)', r'\1' + self.REDACTED + r'\3'),
        ]

        sanitized = url
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


_default_sanitizer = LogSanitizer()


def sanitize(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """Sanitize sensitive data using default sanitizer.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return _default_sanitizer.sanitize_string(data)
    elif isinstance(data, dict):
        return _default_sanitizer.sanitize_dict(data)
    elif isinstance(data, list):
        return _default_sanitizer.sanitize_list(data)
    return data


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Sanitize HTTP headers using default sanitizer.

    Args:
        headers: Headers to sanitize

    Returns:
        Sanitized headers
    """
    return _default_sanitizer.sanitize_headers(headers)


def sanitize_url(url: str) -> str:
    """Sanitize URL using default sanitizer.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL
    """
    return _default_sanitizer.sanitize_url(url)
