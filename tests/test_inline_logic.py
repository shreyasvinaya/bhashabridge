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
async def test_partial_command_shows_filtered_menu(mock_update, mock_context):
    """Partial command prefixes show a command menu filtered by the prefix."""
    # "expl" is a prefix of both "explain" and "explaintranslate", so the menu
    # offers those two options instead of silently returning nothing.
    mock_update.inline_query.query = "expl"

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]

    assert len(results) == 2
    assert all("Explain" in r.title for r in results)


@pytest.mark.asyncio
async def test_full_command_processed(mock_update, mock_context):
    """Test that full valid command is processed."""
    mock_update.inline_query.query = "explain"

    with patch("main._handle_explain", new_callable=AsyncMock) as mock_handle:
        await main.inline_handler(mock_update, mock_context)
        mock_handle.assert_called_once()


@pytest.mark.asyncio
async def test_partial_command_with_space_shows_menu(mock_update, mock_context):
    """A lone prefix token (even with a trailing space) shows the filtered menu."""
    # "e " collapses to the single token "e", a prefix of "explain" and
    # "explaintranslate", so the menu offers those two — it does not explain "e".
    mock_update.inline_query.query = "e "

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 2
    assert all("Explain" in r.title for r in results)


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
async def test_non_command_with_args_shows_full_menu(mock_update, mock_context):
    """A non-command with arguments shows the full command menu (never explains it)."""
    # "hello world" is not a command and has args, so no prefix filter applies —
    # the user gets the full list of commands rather than an explanation of the text.
    mock_update.inline_query.query = "hello world"

    await main.inline_handler(mock_update, mock_context)

    args, _ = mock_update.inline_query.answer.call_args
    results = args[0]
    assert len(results) == 4
