"""Intelligent memory retrieval module for BhashaBridge.

This module provides intelligent retrieval of relevant long-term memories
based on keyword matching and recency scoring. Instead of dumping all
memory into prompts, it selects only the most relevant pieces.
"""

from datetime import datetime, timezone

import long_memory

# Common English stopwords to remove during keyword extraction
STOPWORDS = {
    "the",
    "is",
    "a",
    "to",
    "and",
    "in",
    "it",
    "for",
    "of",
    "on",
    "i",
    "me",
    "my",
    "do",
    "don't",
    "what",
    "how",
    "this",
    "that",
    "you",
    "your",
    "we",
    "our",
    "us",
    "he",
    "she",
    "his",
    "her",
    "him",
    "they",
    "them",
    "their",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "with",
    "at",
    "by",
    "from",
    "as",
    "or",
    "an",
    "are",
    "was",
    "were",
}

# Number of top summaries to retrieve
TOP_K_SUMMARIES = 3
# Maximum notable messages to include
MAX_NOTABLE_MESSAGES = 5
# Minimum score threshold for relevance
MIN_SCORE_THRESHOLD = 0.1


def _extract_keywords(text: str) -> set[str]:
    """Extract keywords from text by removing stopwords.

    Args:
        text: The input text to extract keywords from.

    Returns:
        Set of lowercase keywords (excluding stopwords).

    Example:
        >>> keywords = _extract_keywords("How to say hello in Kanglish")
        >>> "hello" in keywords
        True
        >>> "the" in keywords
        False
    """
    # Convert to lowercase and split on whitespace
    words = text.lower().split()

    # Remove stopwords and non-alphabetic tokens
    keywords = {
        word.strip(".,!?;:\"'()[]{}<>")
        for word in words
        if word.strip(".,!?;:\"'()[]{}<>") not in STOPWORDS
        and len(word.strip(".,!?;:\"'()[]{}<>")) > 0
    }

    return keywords


def _parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO format timestamp string to datetime object.

    Args:
        timestamp_str: ISO format timestamp string.

    Returns:
        Datetime object in UTC.
    """
    # Handle both with and without timezone
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # Fallback to current time if parsing fails
        return datetime.now(timezone.utc)


def _calculate_days_since(timestamp_str: str) -> float:
    """Calculate days since a given timestamp.

    Args:
        timestamp_str: ISO format timestamp string.

    Returns:
        Number of days since the timestamp.
    """
    try:
        timestamp = _parse_timestamp(timestamp_str)
        now = datetime.now(timezone.utc)

        # Ensure both are timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        delta = now - timestamp
        return delta.total_seconds() / (24 * 3600)
    except (ValueError, TypeError):
        return float("inf")


def _score_summary(summary: dict, keywords: set[str]) -> float:
    """Calculate relevance score for a summary.

    Args:
        summary: Summary dictionary with 'key_terms' and 'timestamp' keys.
        keywords: Set of keywords from the target message.

    Returns:
        Combined keyword + recency score between 0 and 1.
    """
    # Keyword overlap score
    summary_keywords = {term.lower() for term in summary.get("key_terms", [])}

    if summary_keywords:
        overlap = len(keywords & summary_keywords)
        keyword_score = overlap / max(len(summary_keywords), 1)
    else:
        keyword_score = 0.0

    # Recency score
    timestamp = summary.get("timestamp", "")
    days_since = _calculate_days_since(timestamp)
    recency_score = 1.0 / (1.0 + days_since)

    # Combined score
    final_score = 0.7 * keyword_score + 0.3 * recency_score

    return final_score


def _format_time_ago(days: float) -> str:
    """Format days into human-readable time ago string.

    Args:
        days: Number of days.

    Returns:
        Human-readable string like "2 days ago" or "just now".
    """
    if days < 1 / 24:  # Less than 1 hour
        return "just now"
    elif days < 1:
        hours = int(days * 24)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif days < 30:
        d = int(days)
        return f"{d} day{'s' if d != 1 else ''} ago"
    elif days < 365:
        months = int(days / 30)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(days / 365)
        return f"{years} year{'s' if years != 1 else ''} ago"


def retrieve_relevant_context(chat_id: int, target_message: str) -> str:
    """Retrieve relevant long-term context for a target message.

    Uses keyword overlap and recency scoring to select the most relevant
    summaries and notable messages from long-term memory.

    Args:
        chat_id: The unique identifier for the chat.
        target_message: The message to find relevant context for.

    Returns:
        Formatted string with relevant context, or empty string if nothing
        relevant is found.

    Example:
        >>> context = retrieve_relevant_context(123456, "macha don't put scene")
        >>> if context:
        ...     print(context)
        [RELEVANT PAST CONTEXT]
        Summary (2 days ago): ...
    """
    # Extract keywords from target message
    keywords = _extract_keywords(target_message)

    if not keywords:
        return ""

    # Load chat memory
    chat_data = long_memory.load_chat_memory(chat_id)
    summaries = chat_data.get("summaries", [])
    notable_messages = chat_data.get("notable_messages", [])

    if not summaries and not notable_messages:
        return ""

    # Score and rank summaries
    scored_summaries = [(summary, _score_summary(summary, keywords)) for summary in summaries]

    # Filter by threshold and sort by score
    relevant_summaries = [
        (s, score) for s, score in scored_summaries if score > MIN_SCORE_THRESHOLD
    ]
    relevant_summaries.sort(key=lambda x: x[1], reverse=True)

    # Take top K
    top_summaries = relevant_summaries[:TOP_K_SUMMARIES]

    # Find relevant notable messages (simple substring match)
    relevant_notable = []
    for msg in notable_messages:
        msg_text = msg.get("text", "").lower()
        explanation = msg.get("explanation", "").lower()

        # Check if any keyword appears in the message or explanation
        if any(kw in msg_text or kw in explanation for kw in keywords):
            relevant_notable.append(msg)

    # Cap at MAX_NOTABLE_MESSAGES
    relevant_notable = relevant_notable[-MAX_NOTABLE_MESSAGES:]

    # If nothing relevant found, return empty string
    if not top_summaries and not relevant_notable:
        return ""

    # Format the output
    lines = ["[RELEVANT PAST CONTEXT]"]

    # Add summaries
    for summary, _score in top_summaries:
        timestamp = summary.get("timestamp", "")
        days_since = _calculate_days_since(timestamp)
        time_ago = _format_time_ago(days_since)
        summary_text = summary.get("summary", "")

        lines.append(f"Summary ({time_ago}): {summary_text}")

    # Add notable messages
    for msg in relevant_notable:
        text = msg.get("text", "")
        explanation = msg.get("explanation", "")
        language_mix = msg.get("language_mix", "Unknown")

        lines.append(f'Notable: "{text}" → means "{explanation}" ({language_mix})')

    return "\n".join(lines)
