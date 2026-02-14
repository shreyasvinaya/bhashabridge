"""Long-term persistent memory module for BhashaBridge.

This module provides persistent storage for conversation summaries and notable
messages using JSON files. Data survives bot restarts.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Base directory for persistent storage
DATA_DIR = Path("data")
CHATS_DIR = DATA_DIR / "chats"
USERS_DIR = DATA_DIR / "users"

# Maximum entries to keep
MAX_SUMMARIES = 50
MAX_NOTABLE_MESSAGES = 100


def _ensure_dirs() -> None:
    """Create data directories if they don't exist."""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    USERS_DIR.mkdir(parents=True, exist_ok=True)


# Ensure directories exist on module load
_ensure_dirs()


def _get_chat_file_path(chat_id: int) -> Path:
    """Get the file path for a chat's memory file."""
    return CHATS_DIR / f"{chat_id}.json"


def _get_user_file_path(user_id: int) -> Path:
    """Get the file path for a user's preferences file."""
    return USERS_DIR / f"{user_id}.json"


def _get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def load_chat_memory(chat_id: int) -> dict:
    """Load chat memory from persistent storage.

    Args:
        chat_id: The unique identifier for the chat.

    Returns:
        Dictionary containing chat memory data with structure:
        {
            "chat_id": int,
            "summaries": list of summary dicts,
            "notable_messages": list of notable message dicts
        }
        Returns default empty structure if file doesn't exist.

    Example:
        >>> data = load_chat_memory(123456)
        >>> data["chat_id"]
        123456
    """
    file_path = _get_chat_file_path(chat_id)

    if not file_path.exists():
        return {
            "chat_id": chat_id,
            "summaries": [],
            "notable_messages": [],
        }

    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        # Return empty structure if file is corrupted
        return {
            "chat_id": chat_id,
            "summaries": [],
            "notable_messages": [],
        }


def save_chat_memory(chat_id: int, data: dict) -> None:
    """Save chat memory to persistent storage.

    Args:
        chat_id: The unique identifier for the chat.
        data: Dictionary containing chat memory data.

    Example:
        >>> data = {"chat_id": 123456, "summaries": [], "notable_messages": []}
        >>> save_chat_memory(123456, data)
    """
    file_path = _get_chat_file_path(chat_id)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_summary(
    chat_id: int,
    summary: str,
    key_terms: list[str],
    participants: list[str],
) -> None:
    """Add a conversation summary to long-term memory.

    Args:
        chat_id: The unique identifier for the chat.
        summary: Text summary of the conversation.
        key_terms: List of slang/code-mixed terms used.
        participants: List of participant names.

    Note:
        Keeps maximum of 50 summaries. Oldest are dropped when limit exceeded.

    Example:
        >>> add_summary(
        ...     123456,
        ...     "Group discussed weekend plans",
        ...     ["macha", "scene"],
        ...     ["Alice", "Bob"]
        ... )
    """
    data = load_chat_memory(chat_id)

    summary_entry = {
        "timestamp": _get_current_timestamp(),
        "summary": summary,
        "key_terms": key_terms,
        "participants": participants,
    }

    data["summaries"].append(summary_entry)

    # Keep only the most recent MAX_SUMMARIES
    if len(data["summaries"]) > MAX_SUMMARIES:
        data["summaries"] = data["summaries"][-MAX_SUMMARIES:]

    save_chat_memory(chat_id, data)


def add_notable_message(
    chat_id: int,
    user: str,
    text: str,
    explanation: str,
    language_mix: str,
) -> None:
    """Add a notable message to long-term memory.

    Args:
        chat_id: The unique identifier for the chat.
        user: The username of the sender.
        text: The original message text.
        explanation: Explanation of the message meaning.
        language_mix: The detected language mix (e.g., "Kanglish", "Hinglish").

    Note:
        Keeps maximum of 100 notable messages. Oldest are dropped when limit exceeded.

    Example:
        >>> add_notable_message(
        ...     123456,
        ...     "Alice",
        ...     "Ayyo don't put scene da",
        ...     "Don't create drama/excuses",
        ...     "Kanglish"
        ... )
    """
    data = load_chat_memory(chat_id)

    message_entry = {
        "timestamp": _get_current_timestamp(),
        "user": user,
        "text": text,
        "explanation": explanation,
        "language_mix": language_mix,
    }

    data["notable_messages"].append(message_entry)

    # Keep only the most recent MAX_NOTABLE_MESSAGES
    if len(data["notable_messages"]) > MAX_NOTABLE_MESSAGES:
        data["notable_messages"] = data["notable_messages"][-MAX_NOTABLE_MESSAGES:]

    save_chat_memory(chat_id, data)


def load_user_prefs(user_id: int) -> dict:
    """Load user preferences from persistent storage.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        Dictionary containing user preferences with structure:
        {
            "user_id": int,
            "preferred_language": str,
            "preferred_tone": str | None,
            "interaction_count": int,
            "last_used": str | None
        }
        Returns default structure if file doesn't exist.

    Example:
        >>> prefs = load_user_prefs(789)
        >>> prefs["preferred_language"]
        'english'
    """
    file_path = _get_user_file_path(user_id)

    if not file_path.exists():
        return {
            "user_id": user_id,
            "preferred_language": "english",
            "preferred_tone": None,
            "interaction_count": 0,
            "last_used": None,
        }

    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {
            "user_id": user_id,
            "preferred_language": "english",
            "preferred_tone": None,
            "interaction_count": 0,
            "last_used": None,
        }


def save_user_prefs(user_id: int, prefs: dict) -> None:
    """Save user preferences to persistent storage.

    Args:
        user_id: The unique identifier for the user.
        prefs: Dictionary containing user preferences.

    Example:
        >>> prefs = {"user_id": 789, "preferred_language": "hindi", ...}
        >>> save_user_prefs(789, prefs)
    """
    file_path = _get_user_file_path(user_id)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


def update_user_prefs(
    user_id: int,
    language: str | None = None,
    tone: str | None = None,
) -> dict:
    """Update user preferences and save to storage.

    Args:
        user_id: The unique identifier for the user.
        language: Optional new preferred language.
        tone: Optional new preferred tone.

    Returns:
        Updated preferences dictionary.

    Example:
        >>> prefs = update_user_prefs(789, language="hindi")
        >>> prefs["preferred_language"]
        'hindi'
    """
    prefs = load_user_prefs(user_id)

    if language is not None:
        prefs["preferred_language"] = language

    if tone is not None:
        prefs["preferred_tone"] = tone

    prefs["interaction_count"] += 1
    prefs["last_used"] = _get_current_timestamp()

    save_user_prefs(user_id, prefs)
    return prefs


def clear_chat_memory(chat_id: int) -> None:
    """Clear all long-term memory for a specific chat.

    Args:
        chat_id: The unique identifier for the chat.

    Example:
        >>> add_summary(123456, "Test summary", [], ["Alice"])
        >>> clear_chat_memory(123456)
        >>> data = load_chat_memory(123456)
        >>> data["summaries"]
        []
    """
    file_path = _get_chat_file_path(chat_id)

    if file_path.exists():
        file_path.unlink()


def clear_user_prefs(user_id: int) -> None:
    """Clear user preferences.

    Args:
        user_id: The unique identifier for the user.

    Example:
        >>> update_user_prefs(789, language="hindi")
        >>> clear_user_prefs(789)
        >>> prefs = load_user_prefs(789)
        >>> prefs["preferred_language"]
        'english'
    """
    file_path = _get_user_file_path(user_id)

    if file_path.exists():
        file_path.unlink()
