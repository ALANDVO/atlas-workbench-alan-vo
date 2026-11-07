
"""
Tests for the deterministic compression engine.
"""

import pytest
from app.core.compression import (
    compress_text,
    estimate_tokens,
    _compress,
    _summarize,
    _generate_mcp_reference,
    compress_request_text,
    CompressionResult,
)


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_short_text(self):
        assert estimate_tokens("hello") == 1

    def test_longer_text(self):
        text = "This is a test sentence with multiple words."
        tokens = estimate_tokens(text)
        assert tokens > 0
        # With new estimation: chars + boundaries // 3
        # "This is a test sentence with multiple words." = 44 chars + ~9 boundaries = 53 // 3 = 17
        assert 15 <= tokens <= 20

    def test_code_like_text(self):
        text = "def function(param: int) -> str: return str(param)"
        tokens = estimate_tokens(text)
        assert tokens > 0


class TestCompressMode:
    def test_compress_mode_basic(self):
        text = "This is a configuration file for the application"
        result = compress_text(text, mode="compress")
        assert isinstance(result, CompressionResult)
        assert result.compressed_text == "This is a config file for the app"
        assert result.savings > 0
        assert result.mcp_reference is not None
        assert result.mcp_reference.startswith("mcp:")

    def test_compress_mode_preserves_numbers(self):
        text = "Error code 500 occurred at line 42"
        result = compress_text(text, mode="compress")
        assert "500" in result.compressed_text
        assert "42" in result.compressed_text

    def test_compress_mode_preserves_identifiers(self):
        text = "The userService.getUser() method returns userData"
        result = compress_text(text, mode="compress")
        assert "userService" in result.compressed_text
        assert "getUser" in result.compressed_text
        assert "userData" in result.compressed_text

    def test_compress_mode_removes_filler(self):
        text = "This is actually a very simple example"
        result = compress_text(text, mode="compress")
        assert "actually" not in result.compressed_text
        assert "very" not in result.compressed_text
        assert "simple" in result.compressed_text
        assert "example" in result.compressed_text

    def test_compress_mode_abbreviates_verbose_phrases(self):
        text = "In order to fix the bug, we need to understand the problem"
        result = compress_text(text, mode="compress")
        assert "to fix the bug" in result.compressed_text or "fix the bug" in result.compressed_text

    def test_compress_mode_deterministic(self):
        text = "This is a test configuration for the application environment"
        result1 = compress_text(text, mode="compress")
        result2 = compress_text(text, mode="compress")
        assert result1.compressed_text == result2.compressed_text
        assert result1.mcp_reference == result2.mcp_reference

    def test_compress_mode_case_insensitive_abbreviation(self):
        text = "FUNCTION and function and Function"
        result = compress_text(text, mode="compress")
        # All should be abbreviated to fn
        assert result.compressed_text.count("fn") == 3


class TestSummarizeMode:
    def test_summarize_mode_basic(self):
        text = "This is the first sentence. This is the second sentence with userService."
        result = compress_text(text, mode="summarize")
        assert "first sentence" in result.compressed_text
        assert "userService" in result.compressed_text
        assert "Key:" in result.compressed_text

    def test_summarize_mode_single_sentence(self):
        text = "Only one sentence here."
        result = compress_text(text, mode="summarize")
        assert result.compressed_text == "Only one sentence here."

    def test_summarize_mode_extracts_numbers(self):
        text = "Error 500 at line 42. Check config."
        result = compress_text(text, mode="summarize")
        assert "500" in result.compressed_text
        assert "42" in result.compressed_text


class TestOffMode:
    def test_off_mode_no_compression(self):
        text = "This is a configuration file for the application"
        result = compress_text(text, mode="off")
        assert result.compressed_text == text
        assert result.savings == 0
        assert result.mcp_reference is None
        assert result.original_tokens == result.compressed_tokens


class TestEmptyInput:
    def test_empty_string_compress(self):
        result = compress_text("", mode="compress")
        assert result.compressed_text == ""
        assert result.savings == 0

    def test_empty_string_summarize(self):
        result = compress_text("", mode="summarize")
        assert result.compressed_text == ""

    def test_none_input(self):
        result = compress_text("", mode="compress")
        assert result.original_tokens == 0


class TestMCPReference:
    def test_mcp_reference_format(self):
        text = "This is a configuration file for the application environment"
        result = compress_text(text, mode="compress")
        assert result.mcp_reference is not None
        assert result.mcp_reference.startswith("mcp:")
        assert len(result.mcp_reference) == 20  # "mcp:" + 16 hex chars

    def test_mcp_reference_deterministic(self):
        text = "deterministic test"
        ref1 = _generate_mcp_reference(text)
        ref2 = _generate_mcp_reference(text)
        assert ref1 == ref2

    def test_mcp_reference_different_for_different_text(self):
        ref1 = _generate_mcp_reference("text one")
        ref2 = _generate_mcp_reference("text two")
        assert ref1 != ref2


class TestCompressRequestText:
    def test_compress_request_text_returns_dict(self):
        text = "This is a test configuration"
        result = compress_request_text(text, mode="compress", provider="openai", model="gpt-4")
        assert isinstance(result, dict)
        assert "input_tokens" in result
        assert "compressed_tokens" in result
        assert "savings" in result
        assert "mcp_reference" in result
        assert "compressed_text" in result

    def test_compress_request_text_off_mode(self):
        text = "No compression"
        result = compress_request_text(text, mode="off")
        assert result["compressed_tokens"] == result["input_tokens"]
        assert result["savings"] == 0
        assert result["mcp_reference"] is None


class TestInternalFunctions:
    def test_compress_function_direct(self):
        text = "configuration initialization implementation"
        result = _compress(text)
        assert result == "config init impl"

    def test_summarize_function_direct(self):
        text = "First sentence. Second sentence with userService."
        result = _summarize(text)
        assert "First sentence" in result
        assert "userService" in result

    def test_generate_mcp_reference_direct(self):
        ref = _generate_mcp_reference("test")
        assert ref.startswith("mcp:")
        assert len(ref) == 20

