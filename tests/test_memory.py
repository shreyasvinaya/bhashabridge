"""Unit tests for memory module."""


import memory


class TestAddMessage:
    """Tests for add_message function."""

    def test_add_single_message(self, sample_chat_id):
        """Test adding a single message."""
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1)

        messages = memory.get_recent_messages(sample_chat_id, 1)
        assert len(messages) == 1
        assert messages[0]["user"] == "Alice"
        assert messages[0]["text"] == "Hello!"
        assert messages[0]["message_id"] == 1
        assert "timestamp" in messages[0]

    def test_add_multiple_messages(self, sample_chat_id):
        """Test adding multiple messages."""
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1)
        memory.add_message(sample_chat_id, "Bob", "Hi!", 2)
        memory.add_message(sample_chat_id, "Charlie", "Hey!", 3)

        messages = memory.get_recent_messages(sample_chat_id, 3)
        assert len(messages) == 3

    def test_max_messages_limit(self, sample_chat_id):
        """Test that max messages limit is enforced."""
        # Add more than MAX_MESSAGES (20)
        for i in range(25):
            memory.add_message(sample_chat_id, f"User{i}", f"Message {i}", i)

        messages = memory.get_recent_messages(sample_chat_id, 25)
        assert len(messages) == 20  # MAX_MESSAGES


class TestGetRecentMessages:
    """Tests for get_recent_messages function."""

    def test_empty_chat(self, sample_chat_id):
        """Test getting messages from empty chat."""
        messages = memory.get_recent_messages(sample_chat_id)
        assert messages == []

    def test_default_n_value(self, sample_chat_id):
        """Test default n value returns 10 messages."""
        for i in range(15):
            memory.add_message(sample_chat_id, f"User{i}", f"Message {i}", i)

        messages = memory.get_recent_messages(sample_chat_id)
        assert len(messages) == 10  # Default n=10

    def test_n_larger_than_messages(self, sample_chat_id):
        """Test n larger than available messages."""
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1)
        memory.add_message(sample_chat_id, "Bob", "Hi!", 2)

        messages = memory.get_recent_messages(sample_chat_id, n=100)
        assert len(messages) == 2

    def test_returns_most_recent(self, sample_chat_id):
        """Test that most recent messages are returned."""
        memory.add_message(sample_chat_id, "Alice", "First", 1)
        memory.add_message(sample_chat_id, "Bob", "Second", 2)
        memory.add_message(sample_chat_id, "Charlie", "Third", 3)

        messages = memory.get_recent_messages(sample_chat_id, n=2)
        assert len(messages) == 2
        assert messages[0]["text"] == "Second"
        assert messages[1]["text"] == "Third"


class TestGetHistoryText:
    """Tests for get_history_text function."""

    def test_empty_chat(self, sample_chat_id):
        """Test empty chat returns empty string."""
        text = memory.get_history_text(sample_chat_id)
        assert text == ""

    def test_format(self, sample_chat_id):
        """Test correct formatting of history."""
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1)
        memory.add_message(sample_chat_id, "Bob", "Hi!", 2)

        text = memory.get_history_text(sample_chat_id)
        expected = "Alice: Hello!\nBob: Hi!"
        assert text == expected


class TestClearHistory:
    """Tests for clear_history function."""

    def test_clear_existing_chat(self, sample_chat_id):
        """Test clearing existing chat history."""
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1)
        memory.clear_history(sample_chat_id)

        messages = memory.get_recent_messages(sample_chat_id)
        assert messages == []

    def test_clear_nonexistent_chat(self, sample_chat_id):
        """Test clearing non-existent chat doesn't raise error."""
        # Should not raise
        memory.clear_history(sample_chat_id)


class TestGetAllChatIds:
    """Tests for get_all_chat_ids function."""

    def test_no_chats(self):
        """Test with no chats."""
        chat_ids = memory.get_all_chat_ids()
        assert chat_ids == []

    def test_multiple_chats(self):
        """Test with multiple chats."""
        memory.add_message(1, "Alice", "Hello", 1)
        memory.add_message(2, "Bob", "Hi", 1)
        memory.add_message(3, "Charlie", "Hey", 1)

        chat_ids = memory.get_all_chat_ids()
        assert set(chat_ids) == {1, 2, 3}


class TestCustomTimestamp:
    """Tests for custom timestamp parameter."""

    def test_custom_timestamp(self, sample_chat_id):
        """Test adding message with custom timestamp."""
        custom_time = "2026-02-14T10:00:00+00:00"
        memory.add_message(sample_chat_id, "Alice", "Hello!", 1, timestamp=custom_time)

        messages = memory.get_recent_messages(sample_chat_id)
        assert messages[0]["timestamp"] == custom_time
