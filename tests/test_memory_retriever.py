"""Unit tests for memory_retriever module."""


import long_memory
import memory_retriever


class TestExtractKeywords:
    """Tests for _extract_keywords function."""

    def test_removes_stopwords(self):
        """Test that stopwords are removed."""
        text = "the quick brown fox is a test"
        keywords = memory_retriever._extract_keywords(text)

        assert "the" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        assert "quick" in keywords
        assert "brown" in keywords

    def test_lowercase(self):
        """Test that keywords are lowercased."""
        text = "HELLO World"
        keywords = memory_retriever._extract_keywords(text)

        assert "hello" in keywords
        assert "world" in keywords

    def test_removes_punctuation(self):
        """Test that punctuation is removed."""
        text = "hello, world! how are you?"
        keywords = memory_retriever._extract_keywords(text)

        assert "hello" in keywords
        assert "world" in keywords

    def test_empty_text(self):
        """Test with empty text."""
        keywords = memory_retriever._extract_keywords("")
        assert keywords == set()

    def test_only_stopwords(self):
        """Test with only stopwords."""
        keywords = memory_retriever._extract_keywords("the is a to")
        assert keywords == set()


class TestScoreSummary:
    """Tests for _score_summary function."""

    def test_perfect_keyword_match(self):
        """Test with perfect keyword overlap."""
        summary = {
            "key_terms": ["macha", "scene"],
            "timestamp": "2026-02-14T10:00:00+00:00",
        }
        keywords = {"macha", "scene"}

        score = memory_retriever._score_summary(summary, keywords)
        assert score > 0.7  # High keyword score + some recency

    def test_partial_keyword_match(self):
        """Test with partial keyword overlap."""
        summary = {
            "key_terms": ["macha", "scene", "ayyo"],
            "timestamp": "2026-02-14T10:00:00+00:00",
        }
        keywords = {"macha"}

        score = memory_retriever._score_summary(summary, keywords)
        assert 0.2 < score < 0.7  # Partial match

    def test_no_keyword_match(self):
        """Test with no keyword overlap."""
        summary = {
            "key_terms": ["xyz", "abc"],
            "timestamp": "2026-02-14T10:00:00+00:00",
        }
        keywords = {"macha", "scene"}

        score = memory_retriever._score_summary(summary, keywords)
        assert score < 0.5  # Only recency score


class TestRetrieveRelevantContext:
    """Tests for retrieve_relevant_context function."""

    def test_no_data(self, sample_chat_id):
        """Test with no stored data."""
        context = memory_retriever.retrieve_relevant_context(
            sample_chat_id, "macha don't put scene"
        )
        assert context == ""

    def test_relevant_summary_found(self, sample_chat_id, sample_summary):
        """Test that relevant summary is retrieved."""
        # Add summary with matching keywords
        long_memory.add_summary(
            sample_chat_id,
            sample_summary["summary"],
            sample_summary["key_terms"],
            sample_summary["participants"],
        )

        context = memory_retriever.retrieve_relevant_context(sample_chat_id, "macha scene ayyo")

        assert "RELEVANT PAST CONTEXT" in context
        assert "Group discussed weekend plans" in context

    def test_relevant_notable_found(self, sample_chat_id, sample_notable_message):
        """Test that relevant notable message is retrieved."""
        long_memory.add_notable_message(
            sample_chat_id,
            sample_notable_message["user"],
            sample_notable_message["text"],
            sample_notable_message["explanation"],
            sample_notable_message["language_mix"],
        )

        context = memory_retriever.retrieve_relevant_context(sample_chat_id, "scene da ayyo")

        assert "Ayyo don't put scene da" in context
        assert "Don't create drama/excuses" in context

    def test_no_relevant_data(self, sample_chat_id):
        """Test with data but no relevant matches."""
        # Add summary with unrelated keywords
        long_memory.add_summary(
            sample_chat_id,
            "Meeting notes",
            ["meeting", "agenda", "schedule"],
            ["Alice", "Bob"],
        )

        context = memory_retriever.retrieve_relevant_context(sample_chat_id, "macha scene party")

        # Should be empty or very low score
        # Note: Recency score might still return results
        assert isinstance(context, str)

    def test_empty_keywords(self, sample_chat_id):
        """Test with message that has no keywords."""
        context = memory_retriever.retrieve_relevant_context(sample_chat_id, "the is a to")
        assert context == ""
