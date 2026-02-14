"""Main entry point for BhashaBridge Telegram bot.

This module sets up the Telegram bot with all handlers for inline mode,
slash commands, and message listening. The bot operates in inline mode
for user-facing features to keep interactions private.
"""

import asyncio
import json
import logging
import os
import uuid

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

import ai_engine
import long_memory
import memory
import memory_retriever

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_LANGUAGES = {
    "english": "English",
    "hindi": "Hindi",
    "kannada": "Kannada",
}

SUMMARY_TRIGGER = 20  # Summarize every 20 messages

# Track messages per chat since last summary
message_counters: dict[int, int] = {}

# Map user_id -> last chat_id they sent a message in
# Used to determine chat context for inline queries
# Persisted to data/user_last_chat.json so it survives restarts
USER_LAST_CHAT_FILE = os.path.join("data", "user_last_chat.json")


def _load_user_last_chat() -> dict[int, int]:
    """Load user->chat mapping from disk."""
    try:
        if os.path.exists(USER_LAST_CHAT_FILE):
            with open(USER_LAST_CHAT_FILE) as f:
                # JSON keys are strings, convert back to int
                return {int(k): int(v) for k, v in json.load(f).items()}
    except Exception as e:
        logger.warning(f"Could not load user_last_chat: {e}")
    return {}


def _save_user_last_chat() -> None:
    """Save user->chat mapping to disk."""
    try:
        os.makedirs(os.path.dirname(USER_LAST_CHAT_FILE), exist_ok=True)
        with open(USER_LAST_CHAT_FILE, "w") as f:
            json.dump({str(k): v for k, v in user_last_chat.items()}, f)
    except Exception as e:
        logger.warning(f"Could not save user_last_chat: {e}")


user_last_chat: dict[int, int] = _load_user_last_chat()

# Recognized tone words for reply command parsing
RECOGNIZED_TONES = {
    "casual",
    "formal",
    "sarcastic",
    "funny",
    "angry",
    "polite",
    "friendly",
    "professional",
    "flirty",
    "chill",
    "playful",
    "affectionate",
    "frustrated",
    "humorous",
    "urgent",
}


def _format_explanation_from_analysis(analysis: dict, translated_text: str | None = None) -> str:
    """Format explanation output from analyze_message response."""
    translation = (
        translated_text
        or analysis.get("translation")
        or analysis.get("translations", {}).get("english", "")
    )
    vibe = (analysis.get("vibe") or "").strip() or "—"
    tone = (analysis.get("tone") or "").strip() or "casual"
    slang = analysis.get("slang") or {}

    lines = [
        f"**🗣️ Translation:** {translation}",
        f"**🎭 Vibe Check:** {vibe}",
        f"**🎵 Tone:** {tone}",
        "**📖 Slang Glossary:**",
    ]

    if slang:
        for term, meaning in slang.items():
            lines.append(f"- {term}: {meaning}")
    else:
        lines.append("- (none)")

    return "\n".join(lines)


def _reply_from_analysis(analysis: dict, requested_tone: str | None = None) -> tuple[str, str]:
    """Pick best reply from analyze_message output.

    Returns:
        tuple(reply_text, tone_used)
    """
    suggested = analysis.get("suggested_replies", {}) or {}

    if requested_tone == "casual":
        casual = suggested.get("casual", {})
        text = casual.get("text", "").strip()
        if text:
            return text, "casual"

    if requested_tone == "formal":
        formal = suggested.get("formal", {})
        text = formal.get("text", "").strip()
        if text:
            return text, "formal"

    matching = suggested.get("matching_tone", {})
    text = (matching.get("text") or "").strip()
    tone_used = (matching.get("tone") or analysis.get("tone") or "casual").strip()
    if text:
        return text, tone_used

    fallback = analysis.get("translation") or "Got it."
    return fallback, tone_used


async def maybe_summarize(chat_id: int) -> None:
    """Summarize conversation to long-term memory if threshold reached.

    Args:
        chat_id: The chat ID to check and potentially summarize.
    """
    message_counters.setdefault(chat_id, 0)
    message_counters[chat_id] += 1

    if message_counters[chat_id] >= SUMMARY_TRIGGER:
        history = memory.get_history_text(chat_id, n=20)
        if history:
            logger.debug("Summarization disabled: Skipping long-term memory storage.")
            # result = ai_engine.summarize_conversation(history)
            # messages = memory.get_recent_messages(chat_id, n=20)
            # participants = list({m["user"] for m in messages})
            # long_memory.add_summary(
            #     chat_id,
            #     result["summary"],
            #     result["key_terms"],
            #     result.get("participants", participants),
            # )
        message_counters[chat_id] = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.

    Sends welcome message with usage instructions.
    """
    bot_username = context.bot.username
    welcome_text = f"""🌉 *BhashaBridge* — Your invisible code-mixed chat translator!

I silently learn your group's conversation and help you understand slang, code-mixed language, and cultural context — all privately via inline mode.

*How to use (type in any chat):*
• `@{bot_username} explain <message>` — Decode a message
• `@{bot_username} explaintranslate hindi <message>` — Explain in Hindi (or kannada)
• `@{bot_username} reply` — Auto-reply based on last 10 messages
• `@{bot_username} reply formal` — Reply in a specific tone
• `@{bot_username} reply formal hindi` — Reply in a specific tone + language
• `@{bot_username} reply hindi` — Reply in a specific language
• `@{bot_username} translate hindi <message>` — Translate to a language
• `@{bot_username} translate kannada <message>` — Translate to Kannada

*Settings (DM the bot):*
• /setlang <english|hindi|kannada> — Set default language
• /settone <casual|formal|...> — Set default reply tone
• /clear — Reset all memory

_Add me to a group and I'll silently learn the conversation!_"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command.

    Clears both short-term and long-term memory for the chat.
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Clear short-term memory
    memory.clear_history(chat_id)

    # Clear long-term memory
    long_memory.clear_chat_memory(chat_id)

    # Clear user preferences
    long_memory.clear_user_prefs(user_id)

    await update.message.reply_text("🧹 All memory cleared!")


async def setlang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setlang command.

    Sets the user's preferred language.
    """
    user_id = update.effective_user.id

    if not context.args:
        langs = ", ".join(SUPPORTED_LANGUAGES.keys())
        await update.message.reply_text(
            f"Please specify a language: {langs}\n\nExample: /setlang hindi"
        )
        return

    language = context.args[0].lower()

    if language not in SUPPORTED_LANGUAGES:
        langs = ", ".join(SUPPORTED_LANGUAGES.keys())
        await update.message.reply_text(f"❌ Unsupported language. Supported: {langs}")
        return

    long_memory.update_user_prefs(user_id, language=language)

    await update.message.reply_text(f"✅ Language set to {SUPPORTED_LANGUAGES[language]}!")


async def settone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settone command.

    Sets or clears the user's preferred default tone.
    """
    user_id = update.effective_user.id

    if not context.args:
        # Clear tone preference if no argument
        long_memory.update_user_prefs(user_id, tone=None)
        await update.message.reply_text("✅ Default tone preference cleared!")
        return

    tone = context.args[0].lower()
    long_memory.update_user_prefs(user_id, tone=tone)

    await update.message.reply_text(f"✅ Default tone set to: {tone}")


async def text_listener(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Listen to and store group messages.

    Silently stores messages in short-term memory and updates user->chat mapping.
    Never replies to messages.
    """
    if not update.message or not update.effective_chat:
        logger.debug("text_listener: skipped — no message or no chat")
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    text = update.message.text
    message_id = update.message.message_id

    logger.info(f"📩 Received message in chat {chat_id} from {username}: {text[:50]}...")

    # Store in short-term memory
    memory.add_message(chat_id, username, text, message_id)

    # Update user -> chat mapping for inline queries
    user_last_chat[user_id] = chat_id
    _save_user_last_chat()

    # Maybe summarize to long-term memory
    await maybe_summarize(chat_id)


async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries.

    Parses inline query and routes to appropriate handler based on command.
    """
    query = update.inline_query.query.strip()
    user_id = update.effective_user.id

    if not query:
        # Empty query - could show help or recent queries
        await update.inline_query.answer([], cache_time=0)
        return

    # Get user's chat context
    chat_id = user_last_chat.get(user_id)

    if not chat_id:
        logger.info(f"No chat context for user {user_id}, proceeding without history.")

    # Recognized commands
    valid_commands = {"explain", "explaintranslate", "reply", "translate"}

    # Parse query into command and arguments
    parts = query.split(maxsplit=1)
    if not parts:
        await update.inline_query.answer([], cache_time=0)
        return

    command = parts[0].lower()

    # Strict command check
    if command not in valid_commands:
        # Ignore invalid/partial commands
        await update.inline_query.answer([], cache_time=0)
        return

    args = parts[1] if len(parts) > 1 else ""

    try:
        if command == "explain":
            await _handle_explain(update, chat_id, args)
        elif command == "explaintranslate":
            await _handle_explaintranslate(update, chat_id, user_id, args)
        elif command == "reply":
            await _handle_reply(update, chat_id, user_id, args)
        elif command == "translate":
            await _handle_translate(update, user_id, args)
    except BadRequest as e:
        # Telegram inline query expired (>10s) — log and move on
        logger.warning(f"Inline query expired before we could answer: {e}")
    except Exception as e:
        logger.error(f"Error handling inline query: {e}")
        try:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="❌ Error",
                    description="Something went wrong. Please try again.",
                    input_message_content=InputTextMessageContent(
                        "⚠️ Sorry, I couldn't process that request. Please try again!"
                    ),
                )
            ]
            await update.inline_query.answer(results, cache_time=0, is_personal=True)
        except BadRequest:
            logger.warning("Could not send error result — inline query already expired.")


async def _handle_explain(update: Update, chat_id: int | None, text: str) -> None:
    """Handle 'explain' inline command."""
    user_provided_text = bool(text)  # True if user typed explicit text after 'explain'

    if not text:
        # If no text provided, explain the latest message using last 10 messages as context
        recent = memory.get_recent_messages(chat_id, n=10) if chat_id else []
        if not recent:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="⚠️ No Messages",
                    description="No recent messages to explain.",
                    input_message_content=InputTextMessageContent(
                        "No recent messages found in this chat."
                    ),
                )
            ]
            await update.inline_query.answer(results, cache_time=0, is_personal=True)
            return
        # Use the most recent message as the target to explain
        text = recent[-1]["text"]

    # Get last 10 messages as conversation context for accurate interpretation
    recent_history = memory.get_history_text(chat_id, n=10) if chat_id else ""
    # long_term_context = memory_retriever.retrieve_relevant_context(chat_id, text) if chat_id else ""
    long_term_context = ""

    # Single AI call (faster than multiple chained calls)
    analysis = await asyncio.to_thread(
        ai_engine.analyze_message, recent_history, long_term_context, text
    )
    explanation = _format_explanation_from_analysis(analysis)

    # Only show "Plain English" when user provided a single explicit message
    # and Gemini confirmed it's plain English. Never skip when using chat context.
    if user_provided_text and analysis.get("is_english") is True:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="👍 Plain English",
                description="That looks like plain English already!",
                input_message_content=InputTextMessageContent(
                    "That message appears to be plain English with no code-mixed content."
                ),
            )
        ]
    else:
        # Store as notable message (extract info from explanation)
        if chat_id is not None:
            long_memory.add_notable_message(
                chat_id,
                "User",
                text,
                explanation[:200],  # Truncate for storage
                analysis.get("detected_language", "Unknown"),
            )

        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔍 Explanation",
                description=explanation[:100] + "...",
                input_message_content=InputTextMessageContent(explanation, parse_mode="Markdown"),
            )
        ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


async def _handle_explaintranslate(
    update: Update, chat_id: int | None, user_id: int, args: str
) -> None:
    """Handle 'explaintranslate' inline command."""
    parts = args.split(maxsplit=1)

    if len(parts) < 2:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ Invalid Format",
                description="Usage: explaintranslate <language> <message>",
                input_message_content=InputTextMessageContent(
                    "Please use: explaintranslate hindi|kannada <message>"
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    target_lang = parts[0].lower()
    text = parts[1]

    # Validate language
    if target_lang not in SUPPORTED_LANGUAGES:
        # Try user's preferred language
        prefs = long_memory.load_user_prefs(user_id)
        target_lang = prefs.get("preferred_language", "english")

    # Get context (empty if no chat context)
    recent_history = memory.get_history_text(chat_id, n=10) if chat_id else ""
    # long_term_context = memory_retriever.retrieve_relevant_context(chat_id, text) if chat_id else ""
    long_term_context = ""

    # Single AI call and reuse returned fields
    analysis = await asyncio.to_thread(
        ai_engine.analyze_message, recent_history, long_term_context, text
    )
    translated_text = (analysis.get("translations") or {}).get(target_lang) or analysis.get(
        "translation", ""
    )
    explanation = _format_explanation_from_analysis(analysis, translated_text=translated_text)

    if analysis.get("is_english") is True:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="👍 Plain English",
                description="That looks like plain English already!",
                input_message_content=InputTextMessageContent(
                    "That message appears to be plain English with no code-mixed content."
                ),
            )
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"🌐 Explain in {SUPPORTED_LANGUAGES.get(target_lang, target_lang)}",
                description=explanation[:100] + "...",
                input_message_content=InputTextMessageContent(explanation, parse_mode="Markdown"),
            )
        ]

        # Reuse precomputed reply from analysis (no extra AI call)
        reply, _ = _reply_from_analysis(analysis)

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"💬 Reply in {SUPPORTED_LANGUAGES.get(target_lang, target_lang)}",
                description=reply[:100],
                input_message_content=InputTextMessageContent(reply),
            )
        )

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


async def _handle_reply(update: Update, chat_id: int | None, user_id: int, args: str) -> None:
    """Handle 'reply' inline command.

    Generates a contextual reply based on the last 10 messages in the chat.
    Uses the predominant language and detected tone from the conversation.
    Optional overrides: reply [tone] [language]
    """
    # Parse optional tone and/or language overrides from args
    tokens = args.split()
    requested_tone: str | None = None
    requested_language: str | None = None

    for token in tokens:
        tok = token.lower()
        if requested_tone is None and tok in RECOGNIZED_TONES:
            requested_tone = tok
        elif requested_language is None and tok in SUPPORTED_LANGUAGES:
            requested_language = tok

    # Get last 10 messages as context
    recent = memory.get_recent_messages(chat_id, n=10) if chat_id else []
    if not recent:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ No Messages",
                description="No recent messages to reply to.",
                input_message_content=InputTextMessageContent(
                    "No recent messages found in this chat."
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    # Build conversation text from last 10 messages
    conversation_text = "\n".join(f"{m['user']}: {m['text']}" for m in recent)
    recent_history = memory.get_history_text(chat_id, n=10) if chat_id else ""
    long_term_context = ""

    # Analyze the conversation to detect predominant tone and language
    analysis = await asyncio.to_thread(
        ai_engine.analyze_message, recent_history, long_term_context, conversation_text
    )
    analyzed_tone = (analysis.get("tone") or "casual").strip().lower()
    analyzed_language = (analysis.get("detected_language") or "english").strip().lower()

    # Map detected language mixes to a base language for reply generation
    if "hinglish" in analyzed_language or "hindi" in analyzed_language:
        predominant_language = "hindi"
    elif "kanglish" in analyzed_language or "kannada" in analyzed_language:
        predominant_language = "kannada"
    else:
        predominant_language = "english"

    # Apply overrides: user-specified > user-prefs > analyzed
    prefs = long_memory.load_user_prefs(user_id)
    tone = requested_tone or prefs.get("preferred_tone") or analyzed_tone
    language = requested_language or predominant_language

    # Generate reply using resolved tone and language
    reply = await asyncio.to_thread(
        ai_engine.generate_reply,
        recent_history,
        long_term_context,
        conversation_text,
        tone,
        language,
    )

    explanation = _format_explanation_from_analysis(analysis)

    lang_label = SUPPORTED_LANGUAGES.get(language, language)
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"💬 Suggested Reply ({tone}, {lang_label})",
            description=reply[:100],
            input_message_content=InputTextMessageContent(reply),
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🔍 Explain First",
            description="Understand the conversation before replying",
            input_message_content=InputTextMessageContent(
                explanation,
                parse_mode="Markdown",
            ),
        ),
    ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


async def _handle_translate(update: Update, user_id: int, args: str) -> None:
    """Handle 'translate' inline command."""
    parts = args.split(maxsplit=1)

    if len(parts) < 2:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ Invalid Format",
                description="Usage: translate <language> <text>",
                input_message_content=InputTextMessageContent(
                    "Please use: translate hindi|kannada|english <text>"
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    target_lang = parts[0].lower()
    text = parts[1]

    # Validate language
    if target_lang not in SUPPORTED_LANGUAGES:
        # Use user's preferred language
        prefs = long_memory.load_user_prefs(user_id)
        target_lang = prefs.get("preferred_language", "english")
        # Treat entire args as text
        text = args

    # Translate (off event loop)
    translation = await asyncio.to_thread(ai_engine.translate_message, text, target_lang)

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"🌐 {SUPPORTED_LANGUAGES.get(target_lang, target_lang)} Translation",
            description=translation[:100],
            input_message_content=InputTextMessageContent(translation),
        )
    ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_TOKEN")

    if not token:
        logger.error("TELEGRAM_TOKEN not found in environment variables!")
        return

    # Build application
    application = ApplicationBuilder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("setlang", setlang_command))
    application.add_handler(CommandHandler("settone", settone_command))

    # Message listener for groups
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            text_listener,
        )
    )

    # Inline query handler
    application.add_handler(InlineQueryHandler(inline_handler))

    # Start the bot
    logger.info("🌉 BhashaBridge is live!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
