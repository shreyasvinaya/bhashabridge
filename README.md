# BhashaBridge 

> **Tagline:** Don't just translate words. Understand the vibe.
> **Event:** Gemini 3 Bengaluru Hackathon
> **Goal:** Build a context-aware Telegram bot (inline mode) that explains Indian code-mixed language (Hinglish, Kanglish, etc.) to English speakers using Gemini, with smart auto-reply generation, tone detection, and multi-language translation.

---

## 0. Prerequisites (Human Setup)

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather). Note the **bot token**.
2. **Enable inline mode** for the bot: send `/setinline` to @BotFather, select your bot, and set a placeholder like `Type to explain, translate, or reply…`.
3. **Disable group privacy mode**: send `/setprivacy` to @BotFather → select your bot → **Disable**. (Required so the bot can read all group messages for context.)
4. Get a **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).
5. Create a `.env` file at the project root:

```env
TELEGRAM_TOKEN=<your-telegram-bot-token>
GEMINI_API_KEY=<your-gemini-api-key>
```

6. Ensure Python ≥ 3.10 is installed.

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
├── memory.py             # Short-term sliding window (in-memory)
├── long_memory.py        # Long-term persistent memory (JSON files)
├── memory_retriever.py   # Intelligent retrieval — selects relevant memories
└── data/                 # Auto-created directory for persistent storage
    ├── chats/            # Per-chat long-term memory JSON files
    └── users/            # Per-user preferences JSON files
```

---

## 2. Step-by-Step Implementation

Execute each step in order. Do not skip ahead.

---

### Step 1: Create `.gitignore`

**File:** `.gitignore`

```
.env
__pycache__/
*.pyc
venv/
.venv/
data/
```

---

### Step 2: Create `requirements.txt`

**File:** `requirements.txt`

```
python-telegram-bot>=20.7,<21
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

Then run:

```bash
pip install -r requirements.txt
```

---

### Step 3: Implement `memory.py` — Short-Term Sliding Window

**File:** `memory.py`

**Purpose:** Store the last N messages per chat in-memory for immediate context.

**Specification:**

- Module-level `dict[int, deque]` called `chat_store`.
- `deque` max length: **20** messages.
- Each stored entry is a `dict` with keys: `user` (str), `text` (str), `timestamp` (ISO 8601 str), `message_id` (int).

**Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `add_message` | `(chat_id: int, user: str, text: str, message_id: int) -> None` | Append a dict `{"user": user, "text": text, "timestamp": <current UTC ISO string>, "message_id": message_id}` to the chat's deque. Create deque if not exists. |
| `get_recent_messages` | `(chat_id: int, n: int = 10) -> list[dict]` | Return the last `n` messages as a list of dicts. Return `[]` if no history. |
| `get_history_text` | `(chat_id: int, n: int = 10) -> str` | Return formatted string of last `n` messages: each line `"{user}: {text}"`. Return `""` if empty. |
| `clear_history` | `(chat_id: int) -> None` | Delete the chat's deque if it exists. No-op otherwise. |

---

### Step 4: Implement `long_memory.py` — Persistent Long-Term Memory

**File:** `long_memory.py`

**Purpose:** Persist conversation summaries and notable messages to JSON files so context survives bot restarts.

**Storage format:**

- Directory: `data/chats/` — one JSON file per chat: `{chat_id}.json`
- Directory: `data/users/` — one JSON file per user: `{user_id}.json`

**Chat memory JSON schema** (`data/chats/{chat_id}.json`):

```json
{
  "chat_id": 123456,
  "summaries": [
    {
      "timestamp": "2026-02-14T10:00:00Z",
      "summary": "Group discussed weekend plans. Lots of Kanglish slang used.",
      "key_terms": ["macha", "scene", "ayyo"],
      "participants": ["Shreyas", "Rahul"]
    }
  ],
  "notable_messages": [
    {
      "timestamp": "2026-02-14T10:05:00Z",
      "user": "Rahul",
      "text": "Ayyo, don't put scene da",
      "explanation": "Don't create drama/excuses",
      "language_mix": "Kanglish"
    }
  ]
}
```

**User preferences JSON schema** (`data/users/{user_id}.json`):

```json
{
  "user_id": 789,
  "preferred_language": "english",
  "preferred_tone": null,
  "interaction_count": 5,
  "last_used": "2026-02-14T10:00:00Z"
}
```

**Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `_ensure_dirs` | `() -> None` | Create `data/chats/` and `data/users/` directories if they don't exist. Call at module load. |
| `load_chat_memory` | `(chat_id: int) -> dict` | Load and return the chat's JSON file. Return a default empty structure if file doesn't exist. |
| `save_chat_memory` | `(chat_id: int, data: dict) -> None` | Write the dict to the chat's JSON file (pretty-printed, `indent=2`). |
| `add_summary` | `(chat_id: int, summary: str, key_terms: list[str], participants: list[str]) -> None` | Append a summary entry to the chat's `summaries` list. Keep max **50** summaries (drop oldest). Save. |
| `add_notable_message` | `(chat_id: int, user: str, text: str, explanation: str, language_mix: str) -> None` | Append to `notable_messages`. Keep max **100** entries (drop oldest). Save. |
| `load_user_prefs` | `(user_id: int) -> dict` | Load user prefs JSON. Return default `{"user_id": user_id, "preferred_language": "english", "preferred_tone": null, "interaction_count": 0, "last_used": null}` if not exists. |
| `save_user_prefs` | `(user_id: int, prefs: dict) -> None` | Write user prefs to JSON file. |
| `update_user_prefs` | `(user_id: int, language: str \| None = None, tone: str \| None = None) -> dict` | Load prefs, update only non-None fields, increment `interaction_count`, set `last_used` to now. Save and return updated prefs. |
| `clear_chat_memory` | `(chat_id: int) -> None` | Delete the chat's JSON file if it exists. |

---

### Step 5: Implement `memory_retriever.py` — Intelligent Memory Retrieval

**File:** `memory_retriever.py`

**Purpose:** Instead of dumping all memory into the prompt, this module selects only the *relevant* pieces of long-term memory based on the current message/query. This keeps our prompts lean and focused.

**Retrieval strategy (keyword + recency scoring):**

1. **Extract keywords** from the target message (split on whitespace, lowercase, remove stopwords like "the", "is", "a", "to", "and", "in", "it", "for", "of", "on", "i", "me", "my", "do", "don't", "what", "how", "this", "that").
2. **Score each summary** from long-term memory:
   - **Keyword overlap score:** Count how many of the summary's `key_terms` appear in the target message keywords. Score = `overlap_count / max(len(key_terms), 1)`.
   - **Recency score:** `1.0 / (1 + days_since_summary)` — more recent = higher score.
   - **Final score:** `0.7 * keyword_score + 0.3 * recency_score`.
3. **Return top-K** summaries (K=3) with score > 0.1.
4. For **notable messages**, do a simple substring match: if any keyword from the target message appears in the notable message's `text` or `explanation`, include it. Cap at 5 notable messages.

**Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `retrieve_relevant_context` | `(chat_id: int, target_message: str) -> str` | Run the retrieval strategy above. Return a formatted string block (see format below). Return `""` if nothing relevant found. |
| `_extract_keywords` | `(text: str) -> set[str]` | Lowercase, split, remove stopwords, return set of remaining words. |
| `_score_summary` | `(summary: dict, keywords: set[str]) -> float` | Compute the combined keyword+recency score. |

**Output format of `retrieve_relevant_context`:**

```
[RELEVANT PAST CONTEXT]
Summary (2 days ago): Group discussed weekend plans. Lots of Kanglish slang used.
Notable: "Ayyo, don't put scene da" → means "Don't create drama/excuses" (Kanglish)
Notable: "Macha come fast" → means "Bro come fast" (Kanglish)
```

If nothing is relevant, return empty string `""` (do NOT include the header).

---

### Step 6: Implement `ai_engine.py` — Gemini Integration

**File:** `ai_engine.py`

**Purpose:** All Gemini API calls. Handles: explain, auto-reply generation (with tone), translation, and conversation summarization.

**Specification:**

1. **Module-level setup:**
   - Load `.env` with `dotenv`.
   - Configure `genai` with `GEMINI_API_KEY`.
   - Instantiate `GenerativeModel` with model `"gemini-2.0-flash"`.
   - Define `SYSTEM_PROMPT` (see below).

2. **System prompt** (`SYSTEM_PROMPT` constant):

```
You are BhashaBridge — an expert linguist and cultural translator for Indian code-mixed languages.
You specialize in Hinglish (Hindi+English), Kanglish (Kannada+English), Tanglish (Tamil+English),
Tenglish (Telugu+English), and other Indian language mixes.

You have three capabilities:
1. EXPLAIN — decode code-mixed messages
2. REPLY — generate contextually appropriate replies
3. TRANSLATE — translate between English, Hindi, and Kannada

Always be concise (max 150 words per response). Use emoji sparingly.
Never fabricate meanings — if unsure, say so.
Consider chat history and past context for accurate interpretation.
```

3. **Required functions:**

| Function | Signature | Behavior |
|---|---|---|
| `analyze_message` | `(recent_history: str, long_term_context: str, target_message: str) -> dict` | **Unified analysis.** Makes a SINGLE Gemini call that returns ALL data needed across every feature. Returns a parsed dict (see schema below). The inline handler calls this once and then picks the relevant fields based on what the user asked for. On exception or JSON parse failure, return a fallback dict with `is_english: True`. |
| `explain_message` | `(recent_history: str, long_term_context: str, target_message: str) -> str` | Explain the target message. See prompt template below. Return `response.text`. On exception: `"⚠️ Couldn't process that. Try again!"`. |
| `explain_with_translate` | `(recent_history: str, long_term_context: str, target_message: str, target_language: str) -> str` | Explain the target message (translation + vibe check + slang glossary + detected tone) but deliver the **entire explanation in `target_language`**. See prompt template below. Return `response.text`. On exception: `"⚠️ Couldn't process that. Try again!"`. |
| `generate_reply` | `(recent_history: str, long_term_context: str, target_message: str, tone: str, language: str) -> str` | Generate a suggested reply to the target message with the specified tone in the specified language. See prompt template below. If a tone and language is not mentioned, take the predominant language and tone from the conversation. Return `response.text`. On exception: `"⚠️ Couldn't generate a reply. Try again!"`. |
| `translate_message` | `(text: str, target_language: str) -> str` | Translate the given text to the target language. See prompt template below. Return `response.text`. On exception: `"⚠️ Couldn't translate. Try again!"`. |
| `summarize_conversation` | `(messages_text: str) -> dict` | Summarize a batch of messages. Return a dict with keys `summary` (str), `key_terms` (list[str]), `participants` (list[str]). Parse the JSON from Gemini's response. On exception, return a fallback dict. |
| `detect_tone` | `(recent_history: str, target_message: str) -> str` | Detect the tone/mood of the target message in context. Return a one-word or short-phrase tone like "casual", "sarcastic", "formal", "angry", "playful", etc. On exception, return `"casual"`. |

> **Design note:** `analyze_message` is the preferred entry point for inline queries because it avoids multiple sequential Gemini calls. The individual functions (`explain_message`, `generate_reply`, etc.) still exist for cases where only one specific capability is needed (e.g., `/setlang` or `/settone` slash commands, `summarize_conversation` for background summarization).

4. **Prompt templates:**

**`analyze_message` prompt:**

```
{long_term_context}

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
- Keep all replies short and natural (1-2 sentences).
- If is_english is true, still fill in all fields (translation = original, slang = {{}}, etc.).
```

**`analyze_message` return dict schema:**

```python
{
    "is_english": bool,           # True if plain English, no code-mixing
    "detected_language": str,     # e.g. "Kanglish", "Hinglish", "English"
    "translation": str,           # English translation
    "vibe": str,                  # Cultural context explanation
    "tone": str,                  # Single-word tone
    "slang": dict[str, str],      # {term: definition}
    "translations": {             # Pre-computed translations
        "english": str,
        "hindi": str,
        "kannada": str
    },
    "suggested_replies": {        # Pre-generated replies
        "matching_tone": {"text": str, "tone": str, "language": str},
        "casual": {"text": str, "language": str},
        "formal": {"text": str, "language": str}
    }
}
```

**How `main.py` uses `analyze_message`:** In the inline handler, call `analyze_message` once. Then based on the user's command:
- **explain** → format `translation`, `vibe`, `tone`, `slang` into the explanation output.
- **explaintranslate <lang>** → use `translations[lang]` for the translated explanation + `tone` + `vibe` + `slang`.
- **reply** / **reply <tone>** → pick from `suggested_replies` (use `matching_tone` if no tone specified, or `casual`/`formal` if specified, or call `generate_reply` for other tones not pre-computed).
- **translate <lang>** → use `translations[lang]`.

This means most inline queries need only **one** Gemini API call instead of multiple.

---

**`explain_message` prompt:**

```
{long_term_context}

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
  - <term>: <definition>
```

**`explain_with_translate` prompt:**

```
{long_term_context}

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
  - <term>: <definition in {target_language}>
```

**`generate_reply` prompt:**

```
{long_term_context}

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
- Output ONLY the reply text, nothing else.
```

**`translate_message` prompt:**

```
[TEXT TO TRANSLATE]
{text}

TASK: Translate the above text to {target_language}.
- If the text is already fully in {target_language}, return it as-is.
- Preserve the meaning, tone, and intent.
- If there are culturally specific terms, translate them naturally (not word-for-word).
- Output ONLY the translated text, nothing else.
```

**`summarize_conversation` prompt:**

```
[CONVERSATION]
{messages_text}

TASK: Summarize this conversation for long-term memory storage.
Respond in this exact JSON format (no markdown fencing):
{{"summary": "<2-3 sentence summary>", "key_terms": ["<slang/code-mixed terms used>"], "participants": ["<names of participants>"]}}
```

**`detect_tone` prompt:**

```
[RECENT CHAT HISTORY]
{recent_history}

[TARGET MESSAGE]
{target_message}

TASK: Detect the tone/mood of the target message given the conversation context.
Respond with ONLY a single word or short phrase describing the tone.
Examples: casual, sarcastic, formal, angry, playful, affectionate, frustrated, humorous, urgent
```

5. **Important implementation details:**
   - Pass `SYSTEM_PROMPT` via the `system_instruction` parameter of `GenerativeModel(...)`, NOT inside user prompts.
   - For `analyze_message`: use `json.loads()` to parse Gemini's response. Strip any markdown code fences (` ```json ... ``` `) before parsing. If parsing fails, return `{"is_english": True, "detected_language": "English", "translation": target_message, "vibe": "", "tone": "casual", "slang": {}, "translations": {"english": target_message, "hindi": "", "kannada": ""}, "suggested_replies": {"matching_tone": {"text": "", "tone": "casual", "language": "english"}, "casual": {"text": "", "language": "english"}, "formal": {"text": "", "language": "english"}}}`.
   - For `summarize_conversation`, use `json.loads()` to parse Gemini's response. If parsing fails, return `{"summary": response.text[:200], "key_terms": [], "participants": []}`.
   - For `detect_tone`, strip whitespace and lowercase the response.
   - **Helper function `_clean_json_response(text: str) -> str`:** Strip leading/trailing whitespace, remove ` ```json ` and ` ``` ` fencing if present. Use this in both `analyze_message` and `summarize_conversation` before calling `json.loads()`.

---

### Step 7: Implement `main.py` — Telegram Bot (Inline Mode)

**File:** `main.py`

**Purpose:** Wire up all Telegram handlers. The bot operates in **inline mode** for user-facing features (explain, reply, translate) so that interactions are private and invisible to other group members.

**How inline mode works for our use case:**
- The bot **silently listens** to all group messages via a regular `MessageHandler` and stores them in memory.
- When a user wants to interact, they **type `@BotUsername` in the chat input field**, which opens an inline query. They type their command after the bot username.
- The bot responds with `InlineQueryResult` articles that only the querying user sees — until/unless the user selects one to post.
- We also keep slash commands (`/start`, `/clear`, `/setlang`, `/settone`) for configuration since those work in private chat with the bot.

**Specification:**

1. **Imports:** `os`, `logging`, `json`, `telegram` (Update, InlineQueryResultArticle, InputTextMessageContent), `telegram.ext` (ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, InlineQueryHandler, filters), `ai_engine`, `memory`, `long_memory`, `memory_retriever`, `dotenv`, `uuid`.

2. **Logging:** Configure at `INFO` level.

3. **Constants:**
   - `SUPPORTED_LANGUAGES = {"english": "English", "hindi": "Hindi", "kannada": "Kannada"}`
   - `SUMMARY_TRIGGER = 20` — summarize to long-term memory every 20 messages.
   - Module-level `message_counters: dict[int, int] = {}` — tracks messages per chat since last summary.

4. **Helper function: `maybe_summarize`**

```python
async def maybe_summarize(chat_id: int):
    """If enough messages have accumulated, summarize and store in long-term memory."""
    message_counters.setdefault(chat_id, 0)
    message_counters[chat_id] += 1
    if message_counters[chat_id] >= SUMMARY_TRIGGER:
        history = memory.get_history_text(chat_id, n=20)
        if history:
            result = ai_engine.summarize_conversation(history)
            messages = memory.get_recent_messages(chat_id, n=20)
            participants = list(set(m["user"] for m in messages))
            long_memory.add_summary(
                chat_id, result["summary"],
                result["key_terms"],
                result.get("participants", participants)
            )
        message_counters[chat_id] = 0
```

5. **Handlers to register:**

| Handler | Type | Trigger | Behavior |
|---|---|---|---|
| `/start` | `CommandHandler` | `/start` | Reply with welcome message (see below). Works in private chat. |
| `/clear` | `CommandHandler` | `/clear` | Clear both short-term and long-term memory for the chat. Reply `"🧹 All memory cleared!"`. |
| `/setlang` | `CommandHandler` | `/setlang <language>` | Parse the language argument. Validate it's in `SUPPORTED_LANGUAGES`. Update user prefs via `long_memory.update_user_prefs`. Reply with confirmation. If invalid, show supported languages. |
| `/settone` | `CommandHandler` | `/settone <tone>` | Set user's preferred default tone. Update user prefs. Reply with confirmation. If no argument given, clear the tone preference (set to `null`). |
| `text_listener` | `MessageHandler` | `filters.TEXT & (~filters.COMMAND) & filters.ChatType.GROUPS` (use `filters.ChatType.SUPERGROUP | filters.ChatType.GROUP`) | Silently store message in short-term memory. Call `maybe_summarize`. **Never reply.** |
| `inline_handler` | `InlineQueryHandler` | Any inline query | Parse the query and route to explain/reply/translate (see detailed spec below). |

6. **`/start` welcome message** (Markdown):

```
🌉 *BhashaBridge* — Your invisible code-mixed chat translator!

I silently learn your group's conversation and help you understand slang, code-mixed language, and cultural context — all privately via inline mode.

*How to use (type in any chat):*
• `@BotUsername explain <message>` — Decode a message
• `@BotUsername explaintranslate hindi <message>` — Explain in Hindi (or kannada)
• `@BotUsername reply <message>` — Get a suggested reply
• `@BotUsername reply formal <message>` — Reply in a specific tone
• `@BotUsername translate hindi <message>` — Translate to a language
• `@BotUsername translate kannada <message>` — Translate to Kannada

*Settings (DM the bot):*
• /setlang <english|hindi|kannada> — Set default language
• /settone <casual|formal|...> — Set default reply tone
• /clear — Reset all memory

_Add me to a group and I'll silently learn the conversation!_
```

Replace `@BotUsername` with the actual bot username dynamically using `context.bot.username`.

7. **Inline query handler — detailed spec:**

The `inline_handler` function receives `update.inline_query.query` (the text the user typed after `@BotUsername `).

**Parse the query** into a command and arguments:

| Query pattern | Action |
|---|---|
| `explain <text>` | Explain the given text (or if text is empty/short, explain the last message in the chat's history). |
| `explaintranslate <language> <text>` | Explain the message AND deliver the explanation in `<language>`. If `<language>` not in SUPPORTED_LANGUAGES, use user's preferred language. Also detects and mentions the tone. |
| `reply <text>` | Auto-detect tone, generate reply for `<text>`. |
| `reply <tone> <text>` | If the first word after "reply" is a recognized tone word (check a set: `casual, formal, sarcastic, funny, angry, polite, friendly, professional, flirty, chill`), use it as tone. Otherwise treat everything as the message text and auto-detect tone. |
| `translate <language> <text>` | Translate `<text>` to `<language>`. If `<language>` is not in SUPPORTED_LANGUAGES, treat the whole thing as text and use user's preferred language. |
| _(anything else)_ | Default: treat entire query as an "explain" request. |

**For each action:**

a. **Explain flow:**
   - Get the user's chat context. Since inline queries don't carry `chat_id` of the group, we need a workaround: use the user's most recent chat from `memory`. Store a mapping `user_last_chat: dict[int, int]` (user_id → last chat_id they sent a message in). Update this in `text_listener`.
   - Get `recent_history` from `memory.get_history_text(chat_id)`.
   - Get `long_term_context` from `memory_retriever.retrieve_relevant_context(chat_id, target_text)`.
   - Call `ai_engine.explain_message(recent_history, long_term_context, target_text)`.
   - If result contains `NO_CONTEXT`, show an inline result saying "That looks like plain English 👍".
   - Otherwise, store the notable message via `long_memory.add_notable_message(...)`.
   - Return the result as an `InlineQueryResultArticle`.

b. **Reply flow:**
   - If no tone specified by user, call `ai_engine.detect_tone(recent_history, target_text)` to auto-detect.
   - Load user prefs for language. If user hasn't set a language, default to `"english"`.
   - If user has a `preferred_tone` set and didn't specify one in the query, use the preferred tone.
   - Call `ai_engine.generate_reply(recent_history, long_term_context, target_text, tone, language)`.
   - **Return TWO inline results:**
     1. The generated reply (title: "💬 Suggested Reply ({tone})")  — selecting this **sends the reply into the chat**.
     2. An explanation of the original message (title: "🔍 Explain First") — in case the user wants to understand before replying.

c. **Explain + Translate flow** (`explaintranslate`):
   - Parse the language from the first word after `explaintranslate`. Validate against `SUPPORTED_LANGUAGES`. If invalid, fall back to user's `preferred_language` from prefs.
   - Get `recent_history` and `long_term_context` (same as explain flow).
   - Call `ai_engine.explain_with_translate(recent_history, long_term_context, target_text, target_language)`.
   - If result contains `NO_CONTEXT`, show "That looks like plain English 👍".
   - Otherwise return the result as an `InlineQueryResultArticle` (title: "🌐 Explain in {language}").
   - **Also return a second inline result:** a suggested reply in the same target language using `ai_engine.generate_reply(...)` with auto-detected tone (title: "💬 Reply in {language}").

d. **Translate flow:**
   - Call `ai_engine.translate_message(target_text, target_language)`.
   - Return the translation as an `InlineQueryResultArticle`.

**Inline result construction:**

```python
InlineQueryResultArticle(
    id=str(uuid.uuid4()),
    title="<title>",
    description="<first 100 chars of result>",
    input_message_content=InputTextMessageContent(
        message_text=result_text,
        parse_mode="Markdown"
    )
)
```

Call `await update.inline_query.answer(results, cache_time=0, is_personal=True)`.
- `is_personal=True` ensures results are specific to the querying user.
- `cache_time=0` ensures fresh results every time.

8. **Critical implementation details:**
   - `text_listener` must update `user_last_chat[update.effective_user.id] = update.effective_chat.id` so inline queries can look up the user's active group.
   - `user_last_chat` is a module-level dict.
   - For Markdown parse mode failures: wrap `answer()` in try/except— if it fails, retry with `parse_mode=None`.
   - **Entry point** (`if __name__ == "__main__"`): Build app, register all handlers, print `"🌉 BhashaBridge is live!"`, call `app.run_polling(allowed_updates=Update.ALL_TYPES)`.
   - The `InlineQueryHandler` must be registered with NO pattern filter (catch all inline queries).
   - `text_listener` should use `filters.UpdateType.MESSAGE & filters.TEXT & ~filters.COMMAND` combined with group chat filters.

---

## 3. Verification Checklist

After all files are created, verify:

### A. Static Checks

- [ ] All 7 files exist: `.gitignore`, `requirements.txt`, `memory.py`, `long_memory.py`, `memory_retriever.py`, `ai_engine.py`, `main.py`
- [ ] `memory.py` and `memory_retriever.py` have no external dependencies beyond stdlib + `long_memory`
- [ ] `long_memory.py` has no external dependencies beyond stdlib
- [ ] `ai_engine.py` imports only `google.generativeai`, `os`, `json`, `dotenv`
- [ ] `main.py` imports from all internal modules correctly
- [ ] No hardcoded API keys or tokens anywhere
- [ ] Python syntax check: `python -m py_compile main.py ai_engine.py memory.py long_memory.py memory_retriever.py`

### B. Runtime Smoke Test

```bash
python main.py
```

Expected: prints `"🌉 BhashaBridge is live!"` and starts polling without errors.

### C. Functional Test Manually

1. Add bot to a Telegram group → sends messages → bot is silent (stores messages)
2. In the group, type `@BotUsername explain macha don't put scene` → see inline results
3. Select a result → only you see the explanation (or it posts if you choose to)
4. Type `@BotUsername reply formal macha don't put scene` → get a formal reply suggestion
5. Type `@BotUsername translate kannada bro come fast` → get Kannada translation
6. DM the bot → `/setlang hindi` → confirmed
7. DM the bot → `/settone casual` → confirmed
8. DM the bot → `/clear` → memory cleared

---

## 4. Feature Summary

| Feature | Implementation |
|---|---|
| **Invisible / Inline Mode** | All user interactions via inline queries — invisible to other group members |
| **Silent Listening** | `text_listener` stores group messages, never replies |
| **On-Demand Explain** | `@Bot explain <msg>` decodes code-mixed messages |
| **Explain in Your Language** | `@Bot explaintranslate hindi <msg>` — full explanation delivered in Hindi/Kannada with tone detection |
| **Smart Auto-Reply** | `@Bot reply <msg>` generates a contextual reply with auto-detected tone |
| **Tone Control** | `@Bot reply formal <msg>` or `/settone` for default tone |
| **Tone Auto-Detection** | If no tone specified, Gemini detects tone from context |
| **Multi-Language Translation** | `@Bot translate hindi/kannada/english <msg>` |
| **Language Preference** | `/setlang` sets default language for replies and translations |
| **Short-Term Memory** | Last 20 messages per chat in-memory sliding window |
| **Smart Retrieval** | Only relevant long-term memories are injected into prompts (keyword + recency scoring) |
| **Auto-Summarization** | Every 20 messages, conversation is auto-summarized to long-term memory |
| **Memory Management** | `/clear` resets both short-term and long-term memory |

---
