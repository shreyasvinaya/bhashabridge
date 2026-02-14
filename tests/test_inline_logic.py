"""Tests for inline query logic to verify the fix for partial command matching."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import main


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.inline_query.answer = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    return context


@pytest.mark.asyncio
async def test_partial_command_ignored(mock_update, mock_context):
    """Test that partial command prefixes are ignored."""
    # "expl" is a prefix of "explain", but not a valid command.
    # Should result in NO result (empty list) or waiting.
    # Current behavior (bug): defaults to 'explain' fallback and returns results.
    # Desired behavior: returns empty list.

    mock_update.inline_query.query = "expl"

    await main.inline_handler(mock_update, mock_context)

    # Verify behavior.
    # If the bug exists, it calls answer with some results (length > 0)
    # If fixed, it should call answer with [] (empty list)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]

    # For now, we expect this to FAIL (returns results) until we fix it.
    # But for the test file itself, I'll write assertions for the DESIRED behavior.
    assert len(results) == 0, "Should ignore partial command 'expl'"


@pytest.mark.asyncio
async def test_full_command_processed(mock_update, mock_context):
    """Test that full valid command is processed."""
    mock_update.inline_query.query = "explain"

    with patch("main._handle_explain", new_callable=AsyncMock) as mock_handle:
        await main.inline_handler(mock_update, mock_context)
        mock_handle.assert_called_once()


@pytest.mark.asyncio
async def test_partial_command_with_space_processed(mock_update, mock_context):
    """Test that partial command with space is processed as content."""
    # "e " -> user finished typing "e". Should explain "e".


async def test_partial_command_with_space_ignored(mock_update, mock_context):
    """Test that partial command with space is ALSO ignored (user preference)."""
    # "e " -> user finished typing "e", but "e" is a prefix of "explain".
    # User requested to NOT explain "e".
    mock_update.inline_query.query = "e "

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 0, "Should ignore 'e ' as it is a single-token prefix"


@pytest.mark.asyncio
async def test_non_command_ignored(mock_update, mock_context):
    """Test that non-commands are completely ignored."""
    # "hello" -> Not a valid command. Should NOT fallback to explain.
    mock_update.inline_query.query = "hello"

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]
    # Check if the result is the help/error message OR empty.
    # The plan says "Return empty results immediately".
    # But wait, if we return empty results, the user sees nothing.
    # That might be confusing if they don't know the commands.
    # However, for "hello", we definitely don't want to explain "hello".
    # I will assert len(results) == 0 based on the "should not return anything" requirement.
    assert len(results) == 0


@pytest.mark.asyncio
async def test_non_command_with_args_ignored(mock_update, mock_context):
    """Test that non-commands with arguments are ignored."""
    # "hello world" -> Should NOT explain "hello world".
    mock_update.inline_query.query = "hello world"

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 0
