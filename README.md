# BhashaBridge — Implementation Plan for Claude Code

> **Tagline:** Don't just translate words. Understand the vibe.
> **Event:** Gemini 3 Bengaluru Hackathon
> **Goal:** Build a context-aware Telegram bot that explains Indian code-mixed language (Hinglish, Kanglish, Tanglish, etc.) to English speakers using Gemini.

---

## 0. Prerequisites (Human Setup — Do Before Running Claude Code)

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather). Note the **bot token**.
2. Get a **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).
3. Create a `.env` file at the project root with:

```env
TELEGRAM_TOKEN=<your-telegram-bot-token>
GEMINI_API_KEY=<your-gemini-api-key>
```

4. Ensure Python ≥ 3.10 is installed.

---

## 1. Project Structure

Create the following files in the project root (`/Users/shreyasv/Desktop/hackathons/bhashabridge/`):

```
bhashabridge/
├── .env                  # (already created by human — DO NOT overwrite)
├── .gitignore
├── requirements.txt
├── main.py               # Telegram bot entry point & handler routing
├── ai_engine.py          # Gemini integration & prompt logic
├── memory.py             # Per-chat sliding-window message history
└── README.md             # This file
```

---

## 2. Step-by-Step Implementation

Execute each step in order. Do not skip ahead.

---

### Step 1: Create `.gitignore`

**File:** `.gitignore`

Contents:

```
.env
__pycache__/
*.pyc
venv/
.venv/
```

---

### Step 2: Create `requirements.txt`

**File:** `requirements.txt`

```
python-telegram-bot>=20.7,<21
google-generativeai>=0.8.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

Then run:

```bash
pip install -r requirements.txt
```

---

### Step 3: Implement `memory.py` — Sliding Window Chat History

**File:** `memory.py`

**Purpose:** Store the last N messages per chat in-memory so the AI has conversational context.

**Specification:**

- Use a module-level `dict[int, deque]` called `chat_store`.
- `deque` max length: **15** messages.
- Each stored entry format: `"FirstName: message text"`.

**Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `add_message` | `(chat_id: int, user: str, text: str) -> None` | Append `"{user}: {text}"` to the chat's deque. Create the deque if it doesn't exist yet. |
| `get_history` | `(chat_id: int) -> str` | Return all messages in the deque joined by `"\n"`. Return empty string `""` if `chat_id` has no history. |
| `clear_history` | `(chat_id: int) -> None` | Delete the chat's deque entry from `chat_store` if it exists. Silently do nothing if it doesn't. |

**Edge cases to handle:**
- `chat_id` not yet in `chat_store` → `get_history` returns `""`, `clear_history` is a no-op.
- Empty `text` → still store it (the user may have sent whitespace).

---

### Step 4: Implement `ai_engine.py` — Gemini Integration

**File:** `ai_engine.py`

**Purpose:** Send chat context + a target message to Gemini and get back a cultural/linguistic explanation.

**Specification:**

1. **Module-level setup:**
   - Load `.env` with `dotenv`.
   - Configure `genai` with the `GEMINI_API_KEY` env var.
   - Instantiate a `GenerativeModel` using model name `"gemini-2.0-flash"`.
   - Define a `SYSTEM_PROMPT` constant (see below).

2. **System prompt** (store as a constant string `SYSTEM_PROMPT`):

```
You are BhashaBridge — an expert linguist and cultural translator for Indian code-mixed languages.
You specialize in Hinglish (Hindi+English), Kanglish (Kannada+English), Tanglish (Tamil+English),
Tenglish (Telugu+English), and other Indian language mixes.

Your job:
- If a message is plain, standard English with no slang or code-mixing, respond with exactly: NO_CONTEXT
- Otherwise, provide:
  **🗣️ Translation:** <literal English meaning>
  **🎭 Vibe Check:** <cultural context — is it sarcasm? affection? frustration? humor?>
  **📖 Slang Glossary:**
  - <term 1>: <definition>
  - <term 2>: <definition>

Rules:
- Be concise. Max 150 words.
- Use emoji sparingly for readability.
- Consider chat history for pronoun resolution and context.
- Never fabricate meanings. If unsure, say so.
```

3. **Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `analyze_message` | `(history: str, target_message: str) -> str` | Build a user prompt combining history and target message (format below). Call `model.generate_content()`. Return `response.text`. On ANY exception, return `"⚠️ Couldn't process that. Try again!"`. |
| `analyze_image` | `(image_bytes: bytes, caption: str \| None) -> str` | Create a PIL Image from bytes. Build a prompt asking to decode any code-mixed text visible in the image (plus optional caption for additional context). Call `model.generate_content([prompt_text, pil_image])`. Return `response.text`. On ANY exception, return `"⚠️ Couldn't read that image. Try again!"`. |

4. **User prompt template for `analyze_message`:**

```
[RECENT CHAT HISTORY]
{history}

[MESSAGE TO EXPLAIN]
{target_message}
```

5. **User prompt template for `analyze_image`:**

```
Analyze this image. It likely contains a screenshot of a chat in an Indian language or code-mixed text.
Decode and explain any non-English or code-mixed text visible in the image.
{f"Additional context from sender: {caption}" if caption else ""}
```

6. **Important implementation details:**
   - Pass `SYSTEM_PROMPT` via the `system_instruction` parameter of `GenerativeModel(...)`, NOT inside the user prompt.
   - Use `google.generativeai` (import as `genai`).
   - Import `PIL.Image` and `io.BytesIO` for image handling.

---

### Step 5: Implement `main.py` — Telegram Bot

**File:** `main.py`

**Purpose:** Wire up Telegram bot handlers, manage message flow, and route to the AI engine.

**Specification:**

1. **Imports:** `os`, `logging`, `telegram` (Update, etc.), `telegram.ext` (ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters), `ai_engine`, `memory`, `dotenv`.

2. **Logging:** Configure logging at `INFO` level with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

3. **Handlers to register (in this order):**

| Handler | Type | Trigger | Behavior |
|---|---|---|---|
| `/start` | `CommandHandler` | `/start` | Reply with a welcome message explaining what the bot does and how to use `/explain`. |
| `/explain` | `CommandHandler` | `/explain` | If the user **replied** to another message, use that replied-to message as the target. Otherwise, use the last message in history. Call `analyze_message(history, target)`. Reply with the result. Skip if result contains `"NO_CONTEXT"`. If NO_CONTEXT, reply with `"That message looks like plain English to me! 👍"`. |
| `/clear` | `CommandHandler` | `/clear` | Call `memory.clear_history(chat_id)`. Reply `"🧹 Context cleared!"`. |
| `text_listener` | `MessageHandler` | `filters.TEXT & (~filters.COMMAND)` | Silently store the message in memory via `add_message`. **Do not reply.** Also check: if the bot's username is @-mentioned in the text, treat it like `/explain` was called. |
| `photo_handler` | `MessageHandler` | `filters.PHOTO` | Download the highest-resolution photo. Call `analyze_image(image_bytes, caption)`. Reply with the result. |

4. **`/start` welcome message** (use Markdown parse mode):

```
🌉 *BhashaBridge* — Your code-mixed chat translator!

I silently listen to group chats and can explain Indian slang, Hinglish, Kanglish, Tanglish, and more.

*How to use:*
• Reply to any confusing message with /explain
• Send me a screenshot of a chat to decode
• Use /clear to reset my memory

_Add me to a group chat to get started!_
```

5. **Critical implementation details:**
   - Use `async def` for all handlers (python-telegram-bot v20+ is fully async).
   - For the `/explain` command: check `update.message.reply_to_message` to see if the user replied to a specific message. If yes, use `update.message.reply_to_message.text` as the target. If no, grab the last message from `memory.get_history()` (split by `\n`, take the last line).
   - For `text_listener`: check if bot username is mentioned via `f"@{context.bot.username}"` (case-insensitive check). If mentioned, strip the mention from the text and run the explain flow.
   - For `photo_handler`: use `await update.message.photo[-1].get_file()` then `await file.download_as_bytearray()` to get bytes.
   - `reply_text` should use `parse_mode="Markdown"`. Wrap in try/except — if Markdown parsing fails, retry without parse_mode.
   - **Entry point** (`if __name__ == "__main__":`): Build the application with `ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()`, register all handlers, print `"🌉 BhashaBridge is live!"`, then call `app.run_polling(allowed_updates=Update.ALL_TYPES)`.

---

## 3. Verification Checklist

After all files are created, verify the following:

### A. Static Checks

- [ ] All 5 files exist: `.gitignore`, `requirements.txt`, `memory.py`, `ai_engine.py`, `main.py`
- [ ] `memory.py` has no external dependencies beyond stdlib
- [ ] `ai_engine.py` imports `google.generativeai`, `PIL.Image`, `io`, `os`, `dotenv`
- [ ] `main.py` imports from `ai_engine` and `memory` correctly
- [ ] No hardcoded API keys or tokens anywhere — all from `.env`
- [ ] Python syntax check passes: `python -m py_compile main.py ai_engine.py memory.py`

### B. Runtime Smoke Test

```bash
python main.py
```

Expected: prints `"🌉 BhashaBridge is live!"` and starts polling without errors (will fail gracefully if `.env` tokens are missing/invalid, but should NOT crash with an unhandled exception).

---

## 4. Feature Summary

| Feature | Implementation |
|---|---|
| **Silent Listening** | `text_listener` stores all group messages, never replies unless triggered |
| **On-Demand Explain** | `/explain` command or @-mention triggers AI analysis |
| **Reply-to-Explain** | Reply to a specific message + `/explain` to target that exact message |
| **Sliding Window Context** | Last 15 messages stored per chat for pronoun/context resolution |
| **Image Decode** | Send a photo (e.g., WhatsApp screenshot) and bot decodes visible text |
| **Cultural Nuance** | System prompt instructs Gemini to explain vibe, sarcasm, emotion — not just translate |
| **Memory Clear** | `/clear` resets context for a chat |

---

## 5. Demo Script (For Judges)

1. **Create Telegram group** "Weekend Plans". Add the bot.
2. **User A** sends: *"Macha, traffic is too much, I'll be late."*
3. **User B** sends: *"Ayyo, don't put scene da. Just come."*
4. **User A** replies to User B's message with `/explain`.
5. **Bot responds** with translation, vibe check, and slang glossary.
6. **Bonus:** Forward a Hindi/Kannada WhatsApp screenshot to the bot → bot decodes it.