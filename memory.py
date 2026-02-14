"""Short-term sliding window memory module for BhashaBridge.

This module provides in-memory storage for recent chat messages using a
sliding window approach with a maximum of 20 messages per chat.
"""

from collections import deque
from datetime import datetime, timezone

# Module-level storage: chat_id -> deque of messages
chat_store: dict[int, deque] = {}

# Maximum number of messages to store per chat
MAX_MESSAGES = 20


def add_message(
    chat_id: int,
    user: str,
    text: str,
    message_id: int,
    timestamp: str | None = None,
) -> None:
    """Add a message to the short-term memory for a chat.

    Args:
        chat_id: The unique identifier for the chat.
        user: The username or display name of the sender.
        text: The message text content.
        message_id: The unique message identifier from Telegram.
        timestamp: Optional ISO 8601 timestamp string. If not provided,
            current UTC time is used.

    Example:
        >>> add_message(123456, "Alice", "Hello macha!", 1)
        >>> add_message(123456, "Bob", "Scene maad beda", 2)
    """
    if chat_id not in chat_store:
        chat_store[chat_id] = deque(maxlen=MAX_MESSAGES)

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    message_entry = {
        "user": user,
        "text": text,
        "timestamp": timestamp,
        "message_id": message_id,
    }

    chat_store[chat_id].append(message_entry)


def get_recent_messages(chat_id: int, n: int = 10) -> list[dict]:
    """Get the most recent n messages from a chat's memory.

    Args:
        chat_id: The unique identifier for the chat.
        n: Number of recent messages to retrieve (default: 10).

    Returns:
        A list of message dictionaries. Returns empty list if chat has no history.

    Example:
        >>> add_message(123456, "Alice", "Hello!", 1)
        >>> get_recent_messages(123456, 1)
        [{'user': 'Alice', 'text': 'Hello!', 'timestamp': '...', 'message_id': 1}]
    """
    if chat_id not in chat_store:
        return []

    # Return the last n messages as a list
    messages = list(chat_store[chat_id])
    return messages[-n:] if n < len(messages) else messages


def get_history_text(chat_id: int, n: int = 10) -> str:
    """Get formatted chat history as a text string.

    Args:
        chat_id: The unique identifier for the chat.
        n: Number of recent messages to include (default: 10).

    Returns:
        Formatted string with each line as "{user}: {text}".
        Returns empty string if chat has no history.

    Example:
        >>> add_message(123456, "Alice", "Hello!", 1)
        >>> add_message(123456, "Bob", "Hi there!", 2)
        >>> get_history_text(123456, 2)
        'Alice: Hello!\nBob: Hi there!'
    """
    messages = get_recent_messages(chat_id, n)
    if not messages:
        return ""

    lines = [f"{msg['user']}: {msg['text']}" for msg in messages]
    return "\n".join(lines)


def clear_history(chat_id: int) -> None:
    """Clear all short-term memory for a specific chat.

    Args:
        chat_id: The unique identifier for the chat.

    Example:
        >>> add_message(123456, "Alice", "Hello!", 1)
        >>> clear_history(123456)
        >>> get_recent_messages(123456)
        []
    """
    if chat_id in chat_store:
        del chat_store[chat_id]


def get_all_chat_ids() -> list[int]:
    """Get a list of all chat IDs currently in memory.

    Returns:
        List of chat IDs that have stored messages.

    Example:
        >>> add_message(123456, "Alice", "Hello!", 1)
        >>> add_message(789012, "Bob", "Hi!", 1)
        >>> get_all_chat_ids()
        [123456, 789012]
    """
    return list(chat_store.keys())
