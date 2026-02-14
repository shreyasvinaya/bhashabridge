"""Tests to verify that long-term memory is disabled."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import main
import memory_retriever
import long_memory


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock()
    update.effective_chat.id = 123456
    update.effective_user.id = 789012
    # inline query mock
    update.inline_query.query = "explain hello"
    update.inline_query.answer = AsyncMock()
    # message mock
    update.message.text = "Hello world"
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    return context


@pytest.mark.asyncio
async def test_summary_generation_disabled(mock_update, mock_context):
    """Test that summary generation is NOT called even if trigger is reached."""
    chat_id = 123456
    main.message_counters[chat_id] = main.SUMMARY_TRIGGER + 1

    # Mock dependencies
    with (
        patch("main.memory.get_history_text", return_value="Some history"),
        patch(
            "main.ai_engine.summarize_conversation",
            return_value={"summary": "sum", "key_terms": [], "participants": []},
        ) as mock_summarize,
        patch("main.long_memory.add_summary") as mock_add_summary,
    ):
        await main.maybe_summarize(chat_id)

        # Expect add_summary to NOT be called
        mock_add_summary.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_disabled_in_explain(mock_update, mock_context):
    """Test that context retrieval is NOT called in explain handler."""
    mock_update.inline_query.query = "explain hello"

    with (
        patch("main.memory_retriever.retrieve_relevant_context") as mock_retrieve,
        patch("main.ai_engine.analyze_message", return_value={"is_english": True}),
    ):
        await main.inline_handler(mock_update, mock_context)

        # Expect retrieve to NOT be called
        mock_retrieve.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_disabled_in_reply(mock_update, mock_context):
    """Test that context retrieval is NOT called in reply handler."""
    mock_update.inline_query.query = "reply hello"

    with (
        patch("main.memory_retriever.retrieve_relevant_context") as mock_retrieve,
        patch("main.ai_engine.analyze_message", return_value={"suggested_replies": {}}),
    ):
        await main.inline_handler(mock_update, mock_context)

        # Expect retrieve to NOT be called
        mock_retrieve.assert_not_called()
