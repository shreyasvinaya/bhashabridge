"""Main entry point for BhashaBridge Telegram bot.

This module sets up the Telegram bot with all handlers for inline mode,
slash commands, and message listening. The bot operates in inline mode
for user-facing features to keep interactions private.
"""

import logging
import os
import uuid

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
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
    level=logging.INFO,
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
user_last_chat: dict[int, int] = {}

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
            result = ai_engine.summarize_conversation(history)
            messages = memory.get_recent_messages(chat_id, n=20)
            participants = list({m["user"] for m in messages})
            long_memory.add_summary(
                chat_id,
                result["summary"],
                result["key_terms"],
                result.get("participants", participants),
            )
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
• `@{bot_username} reply <message>` — Get a suggested reply
• `@{bot_username} reply formal <message>` — Reply in a specific tone
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
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    text = update.message.text
    message_id = update.message.message_id

    # Store in short-term memory
    memory.add_message(chat_id, username, text, message_id)

    # Update user -> chat mapping for inline queries
    user_last_chat[user_id] = chat_id

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
        # User hasn't sent any messages in monitored chats
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ No Chat Context",
                description="Send a message in a group first, then try again.",
                input_message_content=InputTextMessageContent(
                    "I need to see your messages in a group first! Add me to a group and send a message."
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    # Parse query into command and arguments
    parts = query.split(maxsplit=1)
    command = parts[0].lower() if parts else "explain"
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
        else:
            # Default to explain
            await _handle_explain(update, chat_id, query)
    except Exception as e:
        logger.error(f"Error handling inline query: {e}")
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


async def _handle_explain(update: Update, chat_id: int, text: str) -> None:
    """Handle 'explain' inline command."""
    if not text:
        # If no text provided, explain the last message
        recent = memory.get_recent_messages(chat_id, n=1)
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
        text = recent[0]["text"]

    # Get context
    recent_history = memory.get_history_text(chat_id, n=10)
    long_term_context = memory_retriever.retrieve_relevant_context(chat_id, text)

    # Call AI engine
    explanation = ai_engine.explain_message(recent_history, long_term_context, text)

    if "NO_CONTEXT" in explanation:
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
        long_memory.add_notable_message(
            chat_id,
            "User",
            text,
            explanation[:200],  # Truncate for storage
            "Unknown",
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


async def _handle_explaintranslate(update: Update, chat_id: int, user_id: int, args: str) -> None:
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

    # Get context
    recent_history = memory.get_history_text(chat_id, n=10)
    long_term_context = memory_retriever.retrieve_relevant_context(chat_id, text)

    # Get explanation in target language
    explanation = ai_engine.explain_with_translate(
        recent_history, long_term_context, text, target_lang
    )

    if "NO_CONTEXT" in explanation:
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

        # Also add a reply suggestion
        tone = ai_engine.detect_tone(recent_history, text)
        reply = ai_engine.generate_reply(recent_history, long_term_context, text, tone, target_lang)

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"💬 Reply in {SUPPORTED_LANGUAGES.get(target_lang, target_lang)}",
                description=reply[:100],
                input_message_content=InputTextMessageContent(reply),
            )
        )

    await update.inline_query.answer(results, cache_time=0, is_personal=True)


async def _handle_reply(update: Update, chat_id: int, user_id: int, args: str) -> None:
    """Handle 'reply' inline command."""
    parts = args.split(maxsplit=1)

    if not parts:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ Invalid Format",
                description="Usage: reply [tone] <message>",
                input_message_content=InputTextMessageContent(
                    "Please use: reply [casual|formal|...] <message>"
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    # Check if first word is a recognized tone
    maybe_tone = parts[0].lower()
    if maybe_tone in RECOGNIZED_TONES and len(parts) > 1:
        tone = maybe_tone
        text = parts[1]
    else:
        # No tone specified, use default
        text = args
        # Check user preferences
        prefs = long_memory.load_user_prefs(user_id)
        tone = prefs.get("preferred_tone")

        if not tone:
            # Auto-detect tone
            recent_history = memory.get_history_text(chat_id, n=10)
            tone = ai_engine.detect_tone(recent_history, text)

    # Get context
    recent_history = memory.get_history_text(chat_id, n=10)
    long_term_context = memory_retriever.retrieve_relevant_context(chat_id, text)

    # Get user's preferred language
    prefs = long_memory.load_user_prefs(user_id)
    language = prefs.get("preferred_language", "english")

    # Generate reply
    reply = ai_engine.generate_reply(recent_history, long_term_context, text, tone, language)

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"💬 Suggested Reply ({tone})",
            description=reply[:100],
            input_message_content=InputTextMessageContent(reply),
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🔍 Explain First",
            description="Understand the message before replying",
            input_message_content=InputTextMessageContent(
                ai_engine.explain_message(recent_history, long_term_context, text),
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

    # Translate
    translation = ai_engine.translate_message(text, target_lang)

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
