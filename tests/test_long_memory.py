"""Unit tests for long_memory module."""



import long_memory


class TestLoadChatMemory:
    """Tests for load_chat_memory function."""

    def test_nonexistent_chat(self, sample_chat_id):
        """Test loading non-existent chat returns default structure."""
        data = long_memory.load_chat_memory(sample_chat_id)

        assert data["chat_id"] == sample_chat_id
        assert data["summaries"] == []
        assert data["notable_messages"] == []

    def test_existing_chat(self, sample_chat_id):
        """Test loading existing chat data."""
        # Save some data first
        test_data = {
            "chat_id": sample_chat_id,
            "summaries": [{"test": "summary"}],
            "notable_messages": [{"test": "message"}],
        }
        long_memory.save_chat_memory(sample_chat_id, test_data)

        # Load it back
        data = long_memory.load_chat_memory(sample_chat_id)
        assert data["summaries"] == [{"test": "summary"}]

    def test_corrupted_file(self, sample_chat_id):
        """Test handling of corrupted JSON file."""
        # Create corrupted file
        file_path = long_memory._get_chat_file_path(sample_chat_id)
        with open(file_path, "w") as f:
            f.write("not valid json")

        data = long_memory.load_chat_memory(sample_chat_id)
        assert data["chat_id"] == sample_chat_id
        assert data["summaries"] == []


class TestSaveChatMemory:
    """Tests for save_chat_memory function."""

    def test_save_and_load(self, sample_chat_id):
        """Test saving and loading chat memory."""
        test_data = {
            "chat_id": sample_chat_id,
            "summaries": [],
            "notable_messages": [],
        }

        long_memory.save_chat_memory(sample_chat_id, test_data)

        # Verify file exists
        file_path = long_memory._get_chat_file_path(sample_chat_id)
        assert file_path.exists()


class TestAddSummary:
    """Tests for add_summary function."""

    def test_add_single_summary(self, sample_chat_id, sample_summary):
        """Test adding a single summary."""
        long_memory.add_summary(
            sample_chat_id,
            sample_summary["summary"],
            sample_summary["key_terms"],
            sample_summary["participants"],
        )

        data = long_memory.load_chat_memory(sample_chat_id)
        assert len(data["summaries"]) == 1
        assert data["summaries"][0]["summary"] == sample_summary["summary"]
        assert data["summaries"][0]["key_terms"] == sample_summary["key_terms"]
        assert "timestamp" in data["summaries"][0]

    def test_max_summaries_limit(self, sample_chat_id):
        """Test that max summaries limit is enforced."""
        # Add more than MAX_SUMMARIES (50)
        for i in range(55):
            long_memory.add_summary(
                sample_chat_id,
                f"Summary {i}",
                [f"term{i}"],
                [f"User{i}"],
            )

        data = long_memory.load_chat_memory(sample_chat_id)
        assert len(data["summaries"]) == 50
        # Should keep most recent
        assert data["summaries"][-1]["summary"] == "Summary 54"


class TestAddNotableMessage:
    """Tests for add_notable_message function."""

    def test_add_single_message(self, sample_chat_id, sample_notable_message):
        """Test adding a single notable message."""
        long_memory.add_notable_message(
            sample_chat_id,
            sample_notable_message["user"],
            sample_notable_message["text"],
            sample_notable_message["explanation"],
            sample_notable_message["language_mix"],
        )

        data = long_memory.load_chat_memory(sample_chat_id)
        assert len(data["notable_messages"]) == 1
        assert data["notable_messages"][0]["text"] == sample_notable_message["text"]

    def test_max_notable_messages_limit(self, sample_chat_id):
        """Test that max notable messages limit is enforced."""
        # Add more than MAX_NOTABLE_MESSAGES (100)
        for i in range(105):
            long_memory.add_notable_message(
                sample_chat_id,
                f"User{i}",
                f"Message {i}",
                f"Explanation {i}",
                "Kanglish",
            )

        data = long_memory.load_chat_memory(sample_chat_id)
        assert len(data["notable_messages"]) == 100


class TestLoadUserPrefs:
    """Tests for load_user_prefs function."""

    def test_nonexistent_user(self, sample_user_id):
        """Test loading non-existent user returns default prefs."""
        prefs = long_memory.load_user_prefs(sample_user_id)

        assert prefs["user_id"] == sample_user_id
        assert prefs["preferred_language"] == "english"
        assert prefs["preferred_tone"] is None
        assert prefs["interaction_count"] == 0
        assert prefs["last_used"] is None


class TestUpdateUserPrefs:
    """Tests for update_user_prefs function."""

    def test_update_language(self, sample_user_id):
        """Test updating language preference."""
        prefs = long_memory.update_user_prefs(sample_user_id, language="hindi")

        assert prefs["preferred_language"] == "hindi"
        assert prefs["interaction_count"] == 1
        assert prefs["last_used"] is not None

    def test_update_tone(self, sample_user_id):
        """Test updating tone preference."""
        prefs = long_memory.update_user_prefs(sample_user_id, tone="formal")

        assert prefs["preferred_tone"] == "formal"

    def test_increment_interaction_count(self, sample_user_id):
        """Test that interaction count increments."""
        long_memory.update_user_prefs(sample_user_id)
        prefs = long_memory.update_user_prefs(sample_user_id)

        assert prefs["interaction_count"] == 2


class TestClearChatMemory:
    """Tests for clear_chat_memory function."""

    def test_clear_existing(self, sample_chat_id):
        """Test clearing existing chat memory."""
        long_memory.add_summary(sample_chat_id, "Test", [], [])
        long_memory.clear_chat_memory(sample_chat_id)

        file_path = long_memory._get_chat_file_path(sample_chat_id)
        assert not file_path.exists()

    def test_clear_nonexistent(self, sample_chat_id):
        """Test clearing non-existent chat doesn't raise error."""
        long_memory.clear_chat_memory(sample_chat_id)  # Should not raise


class TestClearUserPrefs:
    """Tests for clear_user_prefs function."""

    def test_clear_existing(self, sample_user_id):
        """Test clearing existing user prefs."""
        long_memory.update_user_prefs(sample_user_id, language="hindi")
        long_memory.clear_user_prefs(sample_user_id)

        file_path = long_memory._get_user_file_path(sample_user_id)
        assert not file_path.exists()
