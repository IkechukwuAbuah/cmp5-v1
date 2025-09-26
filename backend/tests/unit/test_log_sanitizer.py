"""Unit tests for log sanitization utilities."""

import pytest
from src.lib.log_sanitizer import LogSanitizer, sanitize, sanitize_headers, sanitize_url


class TestLogSanitizer:
    """Test log sanitization functionality."""

    def setup_method(self):
        """Set up test data."""
        self.sanitizer = LogSanitizer()

    def test_sanitize_api_key(self):
        """Test API key sanitization."""
        text = "api_key=sk-1234567890abcdef"
        result = self.sanitizer.sanitize_string(text)
        assert "sk-1234567890abcdef" not in result
        assert self.sanitizer.REDACTED in result

    def test_sanitize_token(self):
        """Test token sanitization."""
        text = "Bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = self.sanitizer.sanitize_string(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert self.sanitizer.REDACTED in result

    def test_sanitize_password(self):
        """Test password sanitization."""
        text = 'password="my_super_secret_password"'
        result = self.sanitizer.sanitize_string(text)
        assert "my_super_secret_password" not in result
        assert self.sanitizer.REDACTED in result

    def test_sanitize_email_partial_mask(self):
        """Test email partial masking."""
        text = "user@example.com contacted support"
        result = self.sanitizer.sanitize_string(text, partial_mask=True)
        assert "user@example.com" not in result
        assert "@example.com" in result
        assert "us" in result  # First 2 chars visible

    def test_sanitize_phone_partial_mask(self):
        """Test phone number partial masking."""
        text = "Call us at +1-555-123-4567"
        result = self.sanitizer.sanitize_string(text, partial_mask=True)
        assert "555-123" not in result
        assert "4567" in result  # Last 4 digits visible

    def test_sanitize_container_id_partial_mask(self):
        """Test container ID partial masking."""
        text = "Container CSQU3054383 is delayed"
        result = self.sanitizer.sanitize_string(text, partial_mask=True)
        assert "3054383" not in result
        assert "CSQU" in result
        assert "*******" in result

    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {
            "username": "john_doe",
            "password": "secret123",
            "api_key": "sk-abc123",
            "email": "john@example.com",
            "message": "User login successful"
        }

        result = self.sanitizer.sanitize_dict(data)

        assert result["username"] == "john_doe"
        assert result["password"] == self.sanitizer.REDACTED
        assert result["api_key"] == self.sanitizer.REDACTED
        assert "@example.com" in result["email"]
        assert result["message"] == "User login successful"

    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization."""
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret",
                    "token": "bearer-123"
                }
            }
        }

        result = self.sanitizer.sanitize_dict(data)

        assert result["user"]["name"] == "John"
        assert result["user"]["credentials"]["password"] == self.sanitizer.REDACTED
        assert result["user"]["credentials"]["token"] == self.sanitizer.REDACTED

    def test_sanitize_list(self):
        """Test list sanitization."""
        data = [
            "normal text",
            "api_key=secret123",
            {"password": "hidden"},
            ["nested", "token=abc123"]
        ]

        result = self.sanitizer.sanitize_list(data)

        assert result[0] == "normal text"
        assert self.sanitizer.REDACTED in result[1]
        assert result[2]["password"] == self.sanitizer.REDACTED
        assert self.sanitizer.REDACTED in result[3][1]

    def test_sanitize_headers(self):
        """Test HTTP headers sanitization."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "X-API-Key": "sk-1234567890abcdef",
            "User-Agent": "Mozilla/5.0",
            "Cookie": "session=abc123; user=john"
        }

        result = self.sanitizer.sanitize_headers(headers)

        assert result["Content-Type"] == "application/json"
        assert "Bearer" in result["Authorization"]
        assert self.sanitizer.REDACTED in result["Authorization"]
        assert self.sanitizer.REDACTED in result["X-API-Key"]
        assert result["User-Agent"] == "Mozilla/5.0"
        assert self.sanitizer.REDACTED in result["Cookie"]

    def test_sanitize_url(self):
        """Test URL sanitization."""
        # Test query parameter sanitization
        url1 = "https://api.example.com/data?api_key=secret123&user=john"
        result1 = self.sanitizer.sanitize_url(url1)
        assert "secret123" not in result1
        assert self.sanitizer.REDACTED in result1
        assert "user=john" in result1

        # Test auth in URL sanitization
        url2 = "https://user:password123@example.com/path"
        result2 = self.sanitizer.sanitize_url(url2)
        assert "password123" not in result2
        assert self.sanitizer.REDACTED in result2

    def test_sanitize_empty_values(self):
        """Test sanitization of empty values."""
        assert self.sanitizer.sanitize_string("") == ""
        assert self.sanitizer.sanitize_string(None) == None
        assert self.sanitizer.sanitize_dict({}) == {}
        assert self.sanitizer.sanitize_list([]) == []
        assert self.sanitizer.sanitize_headers({}) == {}
        assert self.sanitizer.sanitize_url("") == ""

    def test_custom_patterns(self):
        """Test custom sanitization patterns."""
        import re
        custom_patterns = {
            'custom_id': re.compile(r'\bCUST-\d{6}\b')
        }
        custom_sanitizer = LogSanitizer(custom_patterns=custom_patterns)

        text = "Customer ID: CUST-123456"
        result = custom_sanitizer.sanitize_string(text)
        assert "CUST-123456" not in result
        assert self.sanitizer.REDACTED in result

    def test_custom_keys(self):
        """Test custom sensitive keys."""
        custom_keys = {'client_id', 'secret_key'}
        custom_sanitizer = LogSanitizer(custom_keys=custom_keys)

        data = {
            "client_id": "client123",
            "secret_key": "secret456",
            "public_key": "public789"
        }

        result = custom_sanitizer.sanitize_dict(data)
        assert result["client_id"] == self.sanitizer.REDACTED
        assert result["secret_key"] == self.sanitizer.REDACTED
        assert result["public_key"] == "public789"

    def test_module_functions(self):
        """Test module-level sanitization functions."""
        # Test sanitize function
        assert sanitize("password=secret") != "password=secret"
        assert sanitize({"api_key": "123"})["api_key"] == "***REDACTED***"
        assert "***REDACTED***" in sanitize(["token=abc"])[0]

        # Test sanitize_headers function
        headers = {"Authorization": "Bearer token123"}
        result = sanitize_headers(headers)
        assert "token123" not in result["Authorization"]

        # Test sanitize_url function
        url = "https://api.example.com?api_key=secret"
        result = sanitize_url(url)
        assert "secret" not in result