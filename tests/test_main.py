"""Unit tests for main.py handlers.

These tests use mocked Telegram objects to test the bot handlers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456
    update.effective_user = MagicMock()
    update.effective_user.id = 789012
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.message = MagicMock()
    update.message.text = "Test message"
    update.message.message_id = 1
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.username = "TestBot"
    context.args = []
    return context


class TestStartCommand:
    """Tests for /start command handler."""

    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Test /start command sends welcome message."""
        mock_update.message.reply_text = AsyncMock()

        await main.start_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "BhashaBridge" in call_args[0][0]
        assert "inline mode" in call_args[0][0].lower()


class TestClearCommand:
    """Tests for /clear command handler."""

    @pytest.mark.asyncio
    async def test_clear_command(self, mock_update, mock_context):
        """Test /clear command clears memory."""
        mock_update.message.reply_text = AsyncMock()

        # Add some data first
        import long_memory
        import memory

        memory.add_message(123456, "Test", "Hello", 1)
        long_memory.add_summary(123456, "Test summary", [], ["Test"])

        await main.clear_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("🧹 All memory cleared!")


class TestSetlangCommand:
    """Tests for /setlang command handler."""

    @pytest.mark.asyncio
    async def test_setlang_valid(self, mock_update, mock_context):
        """Test setting language to valid option."""
        mock_context.args = ["hindi"]
        mock_update.message.reply_text = AsyncMock()

        await main.setlang_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "hindi" in mock_update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_setlang_invalid(self, mock_update, mock_context):
        """Test setting language to invalid option."""
        mock_context.args = ["french"]
        mock_update.message.reply_text = AsyncMock()

        await main.setlang_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "Unsupported" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_setlang_no_args(self, mock_update, mock_context):
        """Test /setlang without arguments."""
        mock_context.args = []
        mock_update.message.reply_text = AsyncMock()

        await main.setlang_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "specify" in mock_update.message.reply_text.call_args[0][0].lower()


class TestSettoneCommand:
    """Tests for /settone command handler."""

    @pytest.mark.asyncio
    async def test_settone_with_tone(self, mock_update, mock_context):
        """Test setting tone."""
        mock_context.args = ["formal"]
        mock_update.message.reply_text = AsyncMock()

        await main.settone_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "formal" in mock_update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_settone_clear(self, mock_update, mock_context):
        """Test clearing tone preference."""
        mock_context.args = []
        mock_update.message.reply_text = AsyncMock()

        await main.settone_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "cleared" in mock_update.message.reply_text.call_args[0][0].lower()


class TestTextListener:
    """Tests for text listener handler."""

    @pytest.mark.asyncio
    async def test_message_storage(self, mock_update, mock_context):
        """Test that messages are stored in memory."""
        import memory

        # Clear any existing data
        memory.clear_history(123456)

        await main.text_listener(mock_update, mock_context)

        # Check that message was stored
        messages = memory.get_recent_messages(123456)
        assert len(messages) == 1
        assert messages[0]["text"] == "Test message"

    @pytest.mark.asyncio
    async def test_user_chat_mapping(self, mock_update, mock_context):
        """Test that user->chat mapping is updated."""
        await main.text_listener(mock_update, mock_context)

        # Check that mapping was updated
        assert main.user_last_chat.get(789012) == 123456


class TestMaybeSummarize:
    """Tests for maybe_summarize function."""

    @pytest.mark.asyncio
    async def test_summarize_trigger(self, mock_update, mock_context):
        """Test that summarization triggers after SUMMARY_TRIGGER messages."""
        import memory

        # Clear counter
        main.message_counters[123456] = main.SUMMARY_TRIGGER - 1

        # Add message should trigger summarization
        with patch("main.ai_engine.summarize_conversation") as mock_summarize:
            mock_summarize.return_value = {
                "summary": "Test summary",
                "key_terms": ["test"],
                "participants": ["Test"],
            }

            memory.add_message(123456, "Test", "Hello", 1)
            await main.maybe_summarize(123456)

            # Counter should reset
            assert main.message_counters[123456] == 0


class TestSupportedLanguages:
    """Tests for supported languages constant."""

    def test_supported_languages(self):
        """Test that supported languages are defined."""
        assert "english" in main.SUPPORTED_LANGUAGES
        assert "hindi" in main.SUPPORTED_LANGUAGES
        assert "kannada" in main.SUPPORTED_LANGUAGES


class TestRecognizedTones:
    """Tests for recognized tones."""

    def test_recognized_tones(self):
        """Test that common tones are recognized."""
        assert "casual" in main.RECOGNIZED_TONES
        assert "formal" in main.RECOGNIZED_TONES
        assert "sarcastic" in main.RECOGNIZED_TONES
