"""AI Engine module for BhashaBridge.

This module provides all LLM integrations including message analysis,
explanation, translation, reply generation, and conversation summarization.

Uses LiteLLM so the provider/model is selectable via the ``LLM_MODEL`` env var
without code changes, e.g.::

    LLM_MODEL=groq/llama-3.3-70b-versatile     # default
    LLM_MODEL=openai/gpt-4o-mini
    LLM_MODEL=gemini/gemini-2.5-flash

LiteLLM reads the matching provider key from the environment automatically
(``GROQ_API_KEY``, ``OPENAI_API_KEY``, ``GEMINI_API_KEY``, ...).
"""

import json
import os
import time

import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Let LiteLLM silently drop params a given provider doesn't support, so the same
# call works across providers (e.g. temperature/max_tokens quirks).
litellm.drop_params = True

# Provider-prefixed model. Override with LLM_MODEL to switch providers.
# Default: Llama 3.3 70B on Groq (128K context, free tier available).
MODEL_NAME = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")

# LiteLLM has no persistent client object; instead we check that the API key for
# the selected model's provider is present in the environment.
LLM_AVAILABLE = litellm.validate_environment(MODEL_NAME).get("keys_in_environment", False)

# In-memory cache for repeated inline requests (same user query often sent multiple times)
ANALYSIS_CACHE_TTL_SECONDS = 45
_analysis_cache: dict[str, tuple[float, dict]] = {}

# System prompt for all interactions
SYSTEM_PROMPT = """You are BhashaBridge — an expert linguist and cultural translator for Indian code-mixed languages.
You specialize in Hinglish (Hindi+English), Kanglish (Kannada+English), Tanglish (Tamil+English),
Tenglish (Telugu+English), and other Indian language mixes.

You have three capabilities:
1. EXPLAIN — decode code-mixed messages
2. REPLY — generate contextually appropriate replies
3. TRANSLATE — translate between English, Hindi, and Kannada

Always be concise (max 150 words per response). Use emoji sparingly.
Never fabricate meanings — if unsure, say so.
Consider chat history and past context for accurate interpretation."""


def _call_llm(prompt: str, max_tokens: int = 700) -> str:
    """Make a single LLM call via LiteLLM using the configured ``MODEL_NAME``.

    Args:
        prompt: The user prompt to send.
        max_tokens: Maximum output tokens.

    Returns:
        The raw response text.

    Raises:
        RuntimeError: If no provider credentials are configured for ``MODEL_NAME``.
    """
    if not LLM_AVAILABLE:
        raise RuntimeError(f"No API key configured for model '{MODEL_NAME}'")

    response = litellm.completion(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


def _clean_json_response(text: str) -> str:
    """Clean JSON response by removing markdown code fences.

    Args:
        text: Raw response text from the LLM.

    Returns:
        Cleaned text without markdown fences.
    """
    text = text.strip()

    # Remove ```json and ``` fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def _analysis_cache_key(recent_history: str, long_term_context: str, target_message: str) -> str:
    """Build stable cache key for analysis requests."""
    return "\n||\n".join(
        [recent_history.strip(), long_term_context.strip(), target_message.strip()]
    )


def analyze_message(
    recent_history: str,
    long_term_context: str,
    target_message: str,
) -> dict:
    """Perform comprehensive analysis of a message using a single LLM call.

    This is the preferred entry point for inline queries as it avoids multiple
    sequential API calls by returning all needed data in one response.

    Args:
        recent_history: Formatted string of recent chat messages.
        long_term_context: Relevant long-term memory context.
        target_message: The message to analyze.

    Returns:
        Dictionary with analysis results including:
        - is_english: Whether message is plain English
        - detected_language: Primary language or mix detected
        - translation: English translation
        - vibe: Cultural context explanation
        - tone: Detected tone
        - slang: Dictionary of slang terms and definitions
        - translations: Pre-computed translations to English/Hindi/Kannada
        - suggested_replies: Pre-generated reply suggestions

    Example:
        >>> result = analyze_message("Alice: Hello!", "", "macha don't put scene")
        >>> result["detected_language"]
        'Kanglish'
    """
    if not LLM_AVAILABLE:
        return {
            "is_english": True,
            "detected_language": "English",
            "translation": target_message,
            "vibe": "",
            "tone": "casual",
            "slang": {},
            "translations": {
                "english": target_message,
                "hindi": "",
                "kannada": "",
            },
            "suggested_replies": {
                "matching_tone": {"text": "", "tone": "casual", "language": "english"},
                "casual": {"text": "", "language": "english"},
                "formal": {"text": "", "language": "english"},
            },
        }

    cache_key = _analysis_cache_key(recent_history, long_term_context, target_message)
    cached = _analysis_cache.get(cache_key)
    now = time.time()
    if cached and (now - cached[0]) <= ANALYSIS_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        prompt = f"""{long_term_context}

[RECENT CHAT HISTORY]
{recent_history}

[TARGET MESSAGE]
{target_message}

TASK: Perform a comprehensive analysis of the target message. Return a JSON object (no markdown fencing) with this exact schema:
{{
  "is_english": <true if the message is plain standard English with no slang or code-mixing, false otherwise>,
  "detected_language": "<primary language or mix, e.g. 'Kanglish', 'Hinglish', 'Hindi', 'Kannada', 'English'>",
  "translation": "<literal English translation of the message, or the original text if already English>",
  "vibe": "<cultural context — is it sarcasm? affection? frustration? humor? Explain in 1-2 sentences>",
  "tone": "<single word: casual, sarcastic, formal, angry, playful, affectionate, frustrated, humorous, urgent, etc.>",
  "slang": {{
    "<term1>": "<definition>",
    "<term2>": "<definition>"
  }},
  "translations": {{
    "english": "<full message translated to English>",
    "hindi": "<full message translated to Hindi>",
    "kannada": "<full message translated to Kannada>"
  }},
  "suggested_replies": {{
    "matching_tone": {{"text": "<reply matching detected tone>", "tone": "<the detected tone>", "language": "<same language mix as original>"}},
    "casual": {{"text": "<casual reply>", "language": "english"}},
    "formal": {{"text": "<formal reply>", "language": "english"}}
  }}
}}

Rules:
- "slang" should only contain non-English or code-mixed terms. Empty object {{}} if none.
- "suggested_replies.matching_tone" should mirror the language style of the original message.
- Keep all replies short and natural (1-2 sentences max).
- If is_english is true, still fill in all fields (translation = original, slang = {{}}, etc.).
- Return ONLY valid JSON, no extra text."""

        raw = _call_llm(prompt, max_tokens=700)
        cleaned_text = _clean_json_response(raw)

        parsed = json.loads(cleaned_text)
        _analysis_cache[cache_key] = (now, parsed)

        # Lightweight cache cleanup
        if len(_analysis_cache) > 200:
            expiry = now - ANALYSIS_CACHE_TTL_SECONDS
            stale_keys = [k for k, (ts, _) in _analysis_cache.items() if ts < expiry]
            for key in stale_keys:
                _analysis_cache.pop(key, None)

        return parsed

    except Exception:
        # Return fallback on any error
        return {
            "is_english": True,
            "detected_language": "English",
            "translation": target_message,
            "vibe": "",
            "tone": "casual",
            "slang": {},
            "translations": {
                "english": target_message,
                "hindi": "",
                "kannada": "",
            },
            "suggested_replies": {
                "matching_tone": {"text": "", "tone": "casual", "language": "english"},
                "casual": {"text": "", "language": "english"},
                "formal": {"text": "", "language": "english"},
            },
        }


def explain_message(
    recent_history: str,
    long_term_context: str,
    target_message: str,
) -> str:
    """Explain a code-mixed message.

    Args:
        recent_history: Formatted string of recent chat messages.
        long_term_context: Relevant long-term memory context.
        target_message: The message to explain.

    Returns:
        Formatted explanation string, or "NO_CONTEXT" if plain English.

    Example:
        >>> explain = explain_message("", "", "macha don't put scene")
        >>> "Translation" in explain
        True
    """
    if not LLM_AVAILABLE:
        return "⚠️ LLM not configured. Set the API key for your LLM_MODEL provider in .env"

    try:
        prompt = f"""{long_term_context}

[RECENT CHAT HISTORY]
{recent_history}

[MESSAGE TO EXPLAIN]
{target_message}

TASK: Explain this message for someone who doesn't understand the code-mixed language.
- If the message is plain standard English with no slang or code-mixing, respond with exactly: NO_CONTEXT
- Otherwise provide:
  **🗣️ Translation:** <literal English meaning>
  **🎭 Vibe Check:** <cultural context — sarcasm? affection? frustration? humor?>
  **📖 Slang Glossary:**
  - <term>: <definition>"""

        return _call_llm(prompt)

    except Exception:
        return "⚠️ Couldn't process that. Try again!"


def explain_with_translate(
    recent_history: str,
    long_term_context: str,
    target_message: str,
    target_language: str,
) -> str:
    """Explain a message and deliver the explanation in the target language.

    Args:
        recent_history: Formatted string of recent chat messages.
        long_term_context: Relevant long-term memory context.
        target_message: The message to explain.
        target_language: Language to deliver explanation in (e.g., "hindi", "kannada").

    Returns:
        Formatted explanation in target language, or "NO_CONTEXT" if plain English.

    Example:
        >>> explain = explain_with_translate("", "", "macha", "hindi")
        >>> len(explain) > 0
        True
    """
    if not LLM_AVAILABLE:
        return "⚠️ LLM not configured. Set the API key for your LLM_MODEL provider in .env"

    try:
        prompt = f"""{long_term_context}

[RECENT CHAT HISTORY]
{recent_history}

[MESSAGE TO EXPLAIN]
{target_message}

TASK: Explain this message for someone who doesn't understand the code-mixed language.
Deliver the ENTIRE explanation in {target_language}.
- If the message is plain standard English with no slang or code-mixing, respond with exactly: NO_CONTEXT
- Otherwise provide (all in {target_language}):
  **🗣️ Translation:** <meaning of the message in {target_language}>
  **🎭 Vibe Check:** <cultural context — sarcasm? affection? frustration? humor?>
  **🎵 Tone:** <detected tone of the message, e.g. casual, sarcastic, formal, angry, playful>
  **📖 Slang Glossary:**
  - <term>: <definition in {target_language}>"""

        return _call_llm(prompt)

    except Exception:
        return "⚠️ Couldn't process that. Try again!"


def generate_reply(
    recent_history: str,
    long_term_context: str,
    target_message: str,
    tone: str,
    language: str,
) -> str:
    """Generate a suggested reply to a message.

    Args:
        recent_history: Formatted string of recent chat messages.
        long_term_context: Relevant long-term memory context.
        target_message: The message to reply to.
        tone: Desired tone for the reply.
        language: Target language for the reply.

    Returns:
        Generated reply text.

    Example:
        >>> reply = generate_reply("", "", "macha don't put scene", "formal", "english")
        >>> len(reply) > 0
        True
    """
    if not LLM_AVAILABLE:
        return "⚠️ LLM not configured. Set the API key for your LLM_MODEL provider in .env"

    try:
        prompt = f"""{long_term_context}

[RECENT CHAT HISTORY]
{recent_history}

[MESSAGE TO REPLY TO]
{target_message}

TASK: Generate a natural, contextually appropriate reply to this message.
- Tone: {tone}
- Language: {language}
- The reply should sound like something a real person would say in this conversation.
- Match the conversational register (informal chat, formal, etc.).
- Keep it short and natural (1-2 sentences max).
- Output ONLY the reply text, nothing else."""

        return _call_llm(prompt, max_tokens=150).strip()

    except Exception:
        return "⚠️ Couldn't generate a reply. Try again!"


def translate_message(text: str, target_language: str) -> str:
    """Translate text to the target language.

    Args:
        text: The text to translate.
        target_language: Target language (e.g., "hindi", "kannada", "english").

    Returns:
        Translated text.

    Example:
        >>> translate_message("Hello, how are you?", "hindi")
        '...'
    """
    if not LLM_AVAILABLE:
        return "⚠️ LLM not configured. Set the API key for your LLM_MODEL provider in .env"

    try:
        prompt = f"""[TEXT TO TRANSLATE]
{text}

TASK: Translate the above text to {target_language}.
- If the text is already fully in {target_language}, return it as-is.
- Preserve the meaning, tone, and intent.
- If there are culturally specific terms, translate them naturally (not word-for-word).
- Output ONLY the translated text, nothing else."""

        return _call_llm(prompt).strip()

    except Exception:
        return "⚠️ Couldn't translate. Try again!"


def summarize_chat_context(messages_text: str) -> str:
    """Produce a concise 4-5 line summary of recent chat messages.

    Used by the 'explain' command when no specific message is given.

    Args:
        messages_text: Formatted conversation text (user: message per line).

    Returns:
        A 4-5 line Markdown-formatted summary of the conversation.
    """
    if not LLM_AVAILABLE:
        return "⚠️ LLM not configured. Set the API key for your LLM_MODEL provider in .env"

    try:
        prompt = f"""[CONVERSATION]
{messages_text}

TASK: Summarize this conversation in exactly 4-5 lines. Include:
- **What's being discussed** (main topic/topics)
- **Who's saying what** (key participants and their positions)
- **The overall vibe/tone** (friendly banter, heated argument, casual chat, etc.)
- **Any slang or code-mixed terms** used and what they mean
- **Language(s) used** in the conversation

Format the summary in Markdown with emoji for readability. Be concise but informative.
Do NOT just list out the messages — provide an actual summary."""

        return _call_llm(prompt, max_tokens=400).strip()

    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"summarize_chat_context failed: {e}", exc_info=True)
        return "⚠️ Couldn't summarize the conversation. Try again!"


def summarize_conversation(messages_text: str) -> dict:
    """Summarize a batch of conversation messages.

    Args:
        messages_text: Formatted conversation text to summarize.

    Returns:
        Dictionary with summary, key_terms, and participants.

    Example:
        >>> result = summarize_conversation("Alice: Hello!\\nBob: Hi!")
        >>> "summary" in result
        True
    """
    if not LLM_AVAILABLE:
        return {
            "summary": "API not configured",
            "key_terms": [],
            "participants": [],
        }

    try:
        prompt = f"""[CONVERSATION]
{messages_text}

TASK: Summarize this conversation for long-term memory storage.
Respond in this exact JSON format (no markdown fencing):
{{"summary": "<2-3 sentence summary>", "key_terms": ["<slang/code-mixed terms used>"], "participants": ["<names of participants>"]}}"""

        raw = _call_llm(prompt)
        cleaned_text = _clean_json_response(raw)

        return json.loads(cleaned_text)

    except json.JSONDecodeError:
        return {
            "summary": "Could not summarize",
            "key_terms": [],
            "participants": [],
        }
    except Exception:
        return {
            "summary": "Error during summarization",
            "key_terms": [],
            "participants": [],
        }


def detect_tone(recent_history: str, target_message: str) -> str:
    """Detect the tone/mood of a message.

    Args:
        recent_history: Formatted string of recent chat messages.
        target_message: The message to analyze.

    Returns:
        Single word or short phrase describing the tone.

    Example:
        >>> tone = detect_tone("", "macha don't put scene")
        >>> tone.lower() in ["casual", "sarcastic", "playful"]
        True
    """
    if not LLM_AVAILABLE:
        return "casual"

    try:
        prompt = f"""[RECENT CHAT HISTORY]
{recent_history}

[TARGET MESSAGE]
{target_message}

TASK: Detect the tone/mood of the target message given the conversation context.
Respond with ONLY a single word or short phrase describing the tone.
Examples: casual, sarcastic, formal, angry, playful, affectionate, frustrated, humorous, urgent"""

        return _call_llm(prompt, max_tokens=50).strip().lower()

    except Exception:
        return "casual"
