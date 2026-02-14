"""Integration tests for ai_engine module.

These tests require a valid GEMINI_API_KEY in the environment.
Mark them with @pytest.mark.integration to skip when API is unavailable.
"""

import os

import pytest

import ai_engine

# Check if API key is available
API_KEY_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestAnalyzeMessage:
    """Integration tests for analyze_message function."""

    def test_analyze_kanglish_message(self):
        """Test analyzing a Kanglish message."""
        result = ai_engine.analyze_message(
            recent_history="Alice: Hello\nBob: Hi",
            long_term_context="",
            target_message="macha don't put scene da",
        )
        print(result)
        assert isinstance(result, dict)
        assert "is_english" in result
        assert "detected_language" in result
        assert "translation" in result
        assert "vibe" in result
        assert "tone" in result
        assert "slang" in result
        assert "translations" in result
        assert "suggested_replies" in result

        # Should detect as code-mixed
        assert result["is_english"] is False
        assert result["detected_language"] in [
            "Kanglish",
            "Kannada",
            "English",
            "Tanglish",
            "Tamil",
        ]

    def test_analyze_english_message(self):
        """Test analyzing a plain English message."""
        result = ai_engine.analyze_message(
            recent_history="",
            long_term_context="",
            target_message="Hello, how are you doing today?",
        )

        assert isinstance(result, dict)
        assert result["is_english"] is True
        assert result["detected_language"] == "English"

    def test_fallback_on_error(self, monkeypatch):
        """Test fallback when API fails."""
        # Temporarily break the API client
        original_client = ai_engine.client
        ai_engine.client = None

        result = ai_engine.analyze_message("", "", "test message")

        # Restore client
        ai_engine.client = original_client

        # Should return fallback structure
        assert result["is_english"] is True
        assert result["detected_language"] == "English"


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestExplainMessage:
    """Integration tests for explain_message function."""

    def test_explain_code_mixed(self):
        """Test explaining a code-mixed message."""
        result = ai_engine.explain_message(
            recent_history="",
            long_term_context="",
            target_message="macha scene maadbeda",
        )

        assert isinstance(result, str)
        assert "NO_CONTEXT" not in result
        assert len(result) > 0

    def test_explain_plain_english(self):
        """Test explaining plain English returns NO_CONTEXT."""
        result = ai_engine.explain_message(
            recent_history="",
            long_term_context="",
            target_message="Hello, how are you?",
        )

        assert "NO_CONTEXT" in result


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestExplainWithTranslate:
    """Integration tests for explain_with_translate function."""

    def test_explain_in_hindi(self):
        """Test explaining in Hindi."""
        result = ai_engine.explain_with_translate(
            recent_history="",
            long_term_context="",
            target_message="macha don't put scene",
            target_language="hindi",
        )

        assert isinstance(result, str)
        assert "NO_CONTEXT" not in result
        assert len(result) > 0


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestGenerateReply:
    """Integration tests for generate_reply function."""

    def test_generate_casual_reply(self):
        """Test generating a casual reply."""
        result = ai_engine.generate_reply(
            recent_history="",
            long_term_context="",
            target_message="macha come fast",
            tone="casual",
            language="english",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "⚠️" not in result

    def test_generate_formal_reply(self):
        """Test generating a formal reply."""
        result = ai_engine.generate_reply(
            recent_history="",
            long_term_context="",
            target_message="Hello, how are you?",
            tone="formal",
            language="english",
        )

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestTranslateMessage:
    """Integration tests for translate_message function."""

    def test_translate_to_hindi(self):
        """Test translating to Hindi."""
        result = ai_engine.translate_message(
            text="Hello, how are you?",
            target_language="hindi",
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_translate_to_kannada(self):
        """Test translating to Kannada."""
        result = ai_engine.translate_message(
            text="Where are you going?",
            target_language="kannada",
        )

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestSummarizeConversation:
    """Integration tests for summarize_conversation function."""

    def test_summarize_simple_conversation(self):
        """Test summarizing a simple conversation."""
        messages_text = """Alice: Hey macha!
Bob: Hi, what's up?
Alice: Scene maadbeda, just chilling
Bob: Haha okay"""

        result = ai_engine.summarize_conversation(messages_text)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "key_terms" in result
        assert "participants" in result
        assert isinstance(result["key_terms"], list)
        assert isinstance(result["participants"], list)


@pytest.mark.integration
@pytest.mark.skipif(not API_KEY_AVAILABLE, reason="GEMINI_API_KEY not set")
class TestDetectTone:
    """Integration tests for detect_tone function."""

    def test_detect_casual_tone(self):
        """Test detecting casual tone."""
        result = ai_engine.detect_tone(
            recent_history="",
            target_message="Hey macha, what's up?",
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_detect_sarcastic_tone(self):
        """Test detecting potentially sarcastic tone."""
        result = ai_engine.detect_tone(
            recent_history="",
            target_message="Oh great, another meeting. Just what I needed.",
        )

        assert isinstance(result, str)


class TestCleanJsonResponse:
    """Unit tests for _clean_json_response helper."""

    def test_remove_json_fences(self):
        """Test removing ```json fences."""
        text = '```json\n{"key": "value"}\n```'
        result = ai_engine._clean_json_response(text)
        assert result == '{"key": "value"}'

    def test_remove_generic_fences(self):
        """Test removing ``` fences."""
        text = '```\n{"key": "value"}\n```'
        result = ai_engine._clean_json_response(text)
        assert result == '{"key": "value"}'

    def test_no_fences(self):
        """Test text without fences."""
        text = '{"key": "value"}'
        result = ai_engine._clean_json_response(text)
        assert result == '{"key": "value"}'

    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        text = '  ```json\n{"key": "value"}\n```  '
        result = ai_engine._clean_json_response(text)
        assert result == '{"key": "value"}'
