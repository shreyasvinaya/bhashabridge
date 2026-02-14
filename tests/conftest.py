"""Pytest configuration and fixtures for BhashaBridge tests."""

import tempfile
from datetime import datetime, timezone

import pytest


# Ensure tests use test data directory
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment before each test."""
    # Store original data dir
    original_data_dir = None

    # Import here to avoid circular imports
    import long_memory

    # Store original values
    original_data_dir = long_memory.DATA_DIR

    # Create temporary directory for tests
    with tempfile.TemporaryDirectory() as tmpdir:
        long_memory.DATA_DIR = long_memory.Path(tmpdir)
        long_memory.CHATS_DIR = long_memory.DATA_DIR / "chats"
        long_memory.USERS_DIR = long_memory.DATA_DIR / "users"
        long_memory._ensure_dirs()

        yield

        # Restore original values
        long_memory.DATA_DIR = original_data_dir
        long_memory.CHATS_DIR = original_data_dir / "chats"
        long_memory.USERS_DIR = original_data_dir / "users"


@pytest.fixture
def sample_chat_id():
    """Sample chat ID for testing."""
    return 123456789


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return 987654321


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {
            "user": "Alice",
            "text": "Hello macha!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": 1,
        },
        {
            "user": "Bob",
            "text": "Scene maad beda",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": 2,
        },
        {
            "user": "Charlie",
            "text": "Ayyo don't put scene da",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": 3,
        },
    ]


@pytest.fixture
def sample_summary():
    """Sample summary for testing."""
    return {
        "summary": "Group discussed weekend plans with Kanglish slang",
        "key_terms": ["macha", "scene", "ayyo"],
        "participants": ["Alice", "Bob", "Charlie"],
    }


@pytest.fixture
def sample_notable_message():
    """Sample notable message for testing."""
    return {
        "user": "Bob",
        "text": "Ayyo don't put scene da",
        "explanation": "Don't create drama/excuses",
        "language_mix": "Kanglish",
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token_12345")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_67890")
    return {"TELEGRAM_TOKEN": "test_token_12345", "GEMINI_API_KEY": "test_gemini_key_67890"}


@pytest.fixture(autouse=True)
def clear_memory():
    """Clear memory state before each test."""
    import memory
    import main
    
    # Clear all chat stores
    for chat_id in list(memory.chat_store.keys()):
        memory.clear_history(chat_id)
    
    # Clear main module state
    main.message_counters.clear()
    main.user_last_chat.clear()
    
    yield
    
    # Cleanup after test
    for chat_id in list(memory.chat_store.keys()):
        memory.clear_history(chat_id)
