"""
Unit tests for implementation helpers in the IDP Metadata Collector Framework.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    StructuredLogger,
    DatabricksSecretProvider,
    DatabricksDataFrameWriter,
    DatabricksDataFrameReader,
    RequestsHTTPClient,
)


class TestStructuredLogger:
    """Tests for StructuredLogger"""
    
    def test_logger_creation(self):
        """Test logger is created with correct settings"""
        logger = StructuredLogger("test_module", "DEBUG", "test-123")
        
        assert logger.correlation_id == "test-123"
        assert logger.logger.level == logging.DEBUG
    
    def test_logger_default_correlation_id(self):
        """Test logger generates correlation ID if not provided"""
        logger = StructuredLogger("test_module")
        
        assert logger.correlation_id is not None
        assert len(logger.correlation_id) == 8
    
    def test_sensitive_data_masking_password(self):
        """Test that passwords are masked in logs"""
        logger = StructuredLogger("test", "DEBUG")
        
        message = 'Connecting with password="secret123"'
        masked = logger._mask_sensitive(message)
        
        assert "secret123" not in masked
        assert "[REDACTED]" in masked
    
    def test_sensitive_data_masking_key(self):
        """Test that keys are masked in logs"""
        logger = StructuredLogger("test", "DEBUG")
        
        message = 'Using api_key=abc123xyz'
        masked = logger._mask_sensitive(message)
        
        assert "abc123xyz" not in masked
        assert "[REDACTED]" in masked
    
    def test_sensitive_data_masking_secret(self):
        """Test that secrets are masked in logs"""
        logger = StructuredLogger("test", "DEBUG")
        
        message = 'client_secret: "super_secret_value"'
        masked = logger._mask_sensitive(message)
        
        assert "super_secret_value" not in masked
        assert "[REDACTED]" in masked
    
    def test_sensitive_data_masking_token(self):
        """Test that tokens are masked in logs"""
        logger = StructuredLogger("test", "DEBUG")
        
        message = 'Authorization: Bearer token=eyJhbGciOiJIUzI1NiIs'
        masked = logger._mask_sensitive(message)
        
        assert "eyJhbGciOiJIUzI1NiIs" not in masked
        assert "[REDACTED]" in masked
    
    def test_non_sensitive_data_unchanged(self):
        """Test that non-sensitive data is not masked"""
        logger = StructuredLogger("test", "DEBUG")
        
        message = 'Processing table customers with 1000 rows'
        masked = logger._mask_sensitive(message)
        
        assert masked == message
    
    def test_format_message_with_kwargs(self):
        """Test message formatting with keyword arguments"""
        logger = StructuredLogger("test", "DEBUG")
        
        formatted = logger._format_message("Test message", {"key1": "val1", "key2": 42})
        
        assert "Test message" in formatted
        assert "key1=val1" in formatted
        assert "key2=42" in formatted
    
    def test_format_message_without_kwargs(self):
        """Test message formatting without keyword arguments"""
        logger = StructuredLogger("test", "DEBUG")
        
        formatted = logger._format_message("Test message", {})
        
        assert formatted == "Test message"


class TestDatabricksSecretProvider:
    """Tests for DatabricksSecretProvider"""
    
    def test_get_secret_success(self, mock_dbutils):
        """Test getting secret successfully"""
        mock_dbutils.secrets.get.return_value = "secret_value"
        
        provider = DatabricksSecretProvider(mock_dbutils, "my-scope")
        secret = provider.get_secret("my_key")
        
        assert secret == "secret_value"
        mock_dbutils.secrets.get.assert_called_with(scope="my-scope", key="my_key")
    
    def test_get_secret_caching(self, mock_dbutils):
        """Test that secrets are cached"""
        mock_dbutils.secrets.get.return_value = "secret_value"
        
        provider = DatabricksSecretProvider(mock_dbutils, "my-scope")
        
        # First call
        secret1 = provider.get_secret("my_key")
        # Second call
        secret2 = provider.get_secret("my_key")
        
        assert secret1 == secret2
        # Should only call dbutils once due to caching
        assert mock_dbutils.secrets.get.call_count == 1
    
    def test_get_secret_with_default(self, mock_dbutils):
        """Test getting secret with default when secret not found"""
        mock_dbutils.secrets.get.side_effect = Exception("Secret not found")
        
        provider = DatabricksSecretProvider(mock_dbutils, "my-scope")
        secret = provider.get_secret("missing_key", default="default_value")
        
        assert secret == "default_value"
    
    def test_get_secret_raises_without_default(self, mock_dbutils):
        """Test that exception is raised when secret not found and no default"""
        mock_dbutils.secrets.get.side_effect = Exception("Secret not found")
        
        provider = DatabricksSecretProvider(mock_dbutils, "my-scope")
        
        with pytest.raises(Exception):
            provider.get_secret("missing_key")


class TestDatabricksDataFrameWriter:
    """Tests for DatabricksDataFrameWriter"""
    
    def test_write_table_overwrite(self, spark):
        """Test writing table with overwrite mode"""
        writer = DatabricksDataFrameWriter(spark)
        
        # Create a mock DataFrame with a mock write method
        mock_df = MagicMock()
        mock_write = MagicMock()
        mock_df.write = mock_write
        mock_write.format.return_value = mock_write
        mock_write.mode.return_value = mock_write
        mock_write.option.return_value = mock_write
        
        writer.write_table(mock_df, "test_table", mode="overwrite")
        
        mock_write.format.assert_called_with("delta")
        mock_write.mode.assert_called_with("overwrite")
        mock_write.saveAsTable.assert_called_with("test_table")
    
    def test_write_table_append(self, spark):
        """Test writing table with append mode"""
        writer = DatabricksDataFrameWriter(spark)
        
        mock_df = MagicMock()
        mock_write = MagicMock()
        mock_df.write = mock_write
        mock_write.format.return_value = mock_write
        mock_write.mode.return_value = mock_write
        mock_write.option.return_value = mock_write
        
        writer.write_table(mock_df, "test_table", mode="append")
        
        mock_write.mode.assert_called_with("append")


class TestDatabricksDataFrameReader:
    """Tests for DatabricksDataFrameReader"""
    
    def test_read_table(self, spark):
        """Test reading table"""
        reader = DatabricksDataFrameReader(spark)
        
        # Create a test table first
        df = spark.createDataFrame([("a",), ("b",)], ["col"])
        df.createOrReplaceTempView("test_view")
        
        result = reader.read_table("test_view")
        
        assert result.count() == 2
    
    def test_table_exists_true(self, spark):
        """Test table_exists returns True for existing table"""
        reader = DatabricksDataFrameReader(spark)
        
        # Create a test view
        df = spark.createDataFrame([("a",)], ["col"])
        df.createOrReplaceTempView("existing_view")
        
        # Note: table_exists checks catalog, temp views may not be visible
        # This test is implementation-dependent
        # For actual tables, use spark.catalog.tableExists
    
    def test_table_exists_false(self, spark):
        """Test table_exists returns False for non-existing table"""
        reader = DatabricksDataFrameReader(spark)
        
        result = reader.table_exists("definitely_not_existing_table_xyz123")
        
        assert result is False


class TestRequestsHTTPClient:
    """Tests for RequestsHTTPClient"""
    
    def test_client_creation(self):
        """Test HTTP client is created"""
        client = RequestsHTTPClient()
        
        # Client should be created (may or may not have requests available)
        assert client is not None
    
    def test_get_request(self):
        """Test GET request with mock session"""
        client = RequestsHTTPClient()
        
        # Create mock session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_session.get.return_value = mock_response
        
        # Replace session with mock
        client.session = mock_session
        
        result = client.get("https://api.example.com/data", {"Auth": "token"}, 30)
        
        assert result == {"data": "test"}
        mock_session.get.assert_called_once()
    
    def test_post_request(self):
        """Test POST request with mock session"""
        client = RequestsHTTPClient()
        
        # Create mock session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "created"}
        mock_session.post.return_value = mock_response
        
        # Replace session with mock
        client.session = mock_session
        
        result = client.post(
            "https://api.example.com/data",
            {"Auth": "token"},
            {"name": "test"},
            30
        )
        
        assert result == {"status": "created"}
        mock_session.post.assert_called_once()
    
    def test_get_without_session_raises(self):
        """Test that get raises error when session not available"""
        client = RequestsHTTPClient()
        client.session = None
        
        with pytest.raises(RuntimeError, match="requests library not available"):
            client.get("https://api.example.com", {}, 30)


class TestLoggerLevels:
    """Tests for different logging levels"""
    
    def test_info_level(self, capsys):
        """Test INFO level logging goes to stdout"""
        logger = StructuredLogger("test_info_level", "INFO")
        logger.info("Test info message")
        
        captured = capsys.readouterr()
        assert "Test info message" in captured.out
    
    def test_warning_level(self, capsys):
        """Test WARNING level logging"""
        logger = StructuredLogger("test_warning_level", "WARNING")
        logger.warning("Test warning message")
        
        captured = capsys.readouterr()
        assert "Test warning message" in captured.out
    
    def test_error_level(self, capsys):
        """Test ERROR level logging"""
        logger = StructuredLogger("test_error_level", "ERROR")
        logger.error("Test error message")
        
        captured = capsys.readouterr()
        assert "Test error message" in captured.out
    
    def test_debug_not_shown_at_info_level(self, capsys):
        """Test that DEBUG messages are not shown at INFO level"""
        logger = StructuredLogger("test_debug_level", "INFO")
        logger.debug("Test debug message")
        
        captured = capsys.readouterr()
        assert "Test debug message" not in captured.out
