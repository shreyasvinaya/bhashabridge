Architecture
============

System overview and design documentation for BhashaBridge.

High-Level Architecture
-----------------------

.. mermaid::

   graph TB
       subgraph Telegram
           User[User]
           Group[Group Chat]
       end
       
       subgraph BhashaBridge
           Bot[Telegram Bot]
           Handlers[Message Handlers]
           Inline[Inline Query Handler]
           Memory[Memory Manager]
           AI[AI Engine]
       end
       
       subgraph Storage
           ShortTerm[Short-Term Memory<br/>In-Memory Deque]
           LongTerm[Long-Term Memory<br/>JSON Files]
       end
       
       subgraph External
           Gemini[Google Gemini API]
       end
       
       User -->|Inline Query| Bot
       Group -->|Messages| Bot
       Bot --> Handlers
       Bot --> Inline
       Handlers --> Memory
       Inline --> AI
       Inline --> Memory
       Memory --> ShortTerm
       Memory --> LongTerm
       AI --> Gemini

Component Overview
------------------

The system consists of 7 core modules:

1. **main.py** - Telegram bot entry point and handlers
2. **ai_engine.py** - Gemini API integration
3. **memory.py** - Short-term sliding window memory
4. **long_memory.py** - Long-term persistent storage
5. **memory_retriever.py** - Intelligent memory retrieval
6. **tests/** - Comprehensive test suite
7. **docs/** - Sphinx documentation

Module Interactions
-------------------

.. mermaid::

   graph LR
       main[main.py]
       ai[ai_engine.py]
       mem[memory.py]
       long[long_memory.py]
       ret[memory_retriever.py]
       
       main -->|uses| ai
       main -->|uses| mem
       main -->|uses| long
       main -->|uses| ret
       ai -->|retrieves context| ret
       ret -->|loads| long
       main -->|summarizes| long

Data Flow
---------

Message Flow
~~~~~~~~~~~~

.. mermaid::

   sequenceDiagram
       participant U as User
       participant T as Telegram
       participant B as Bot
       participant M as Memory
       participant AI as AI Engine
       
       U->>T: Send message in group
       T->>B: Forward message
       B->>M: Store in short-term
       B->>M: Update user->chat mapping
       alt Every 20 messages
           B->>AI: Summarize conversation
           AI-->>B: Summary + key_terms
           B->>M: Save to long-term
       end

Inline Query Flow
~~~~~~~~~~~~~~~~~

.. mermaid::

   sequenceDiagram
       participant U as User
       participant T as Telegram
       participant B as Bot
       participant R as Retriever
       participant M as Memory
       participant AI as AI Engine
       
       U->>T: Type @Bot explain message
       T->>B: Inline query
       B->>M: Get user's chat context
       B->>M: Get recent messages
       B->>R: Retrieve relevant long-term
       R->>M: Load summaries/notable
       M-->>R: Return matches
       R-->>B: Return formatted context
       B->>AI: Analyze message
       AI-->>B: Return analysis
       B->>T: Return inline results
       T->>U: Show suggestions

Memory Architecture
-------------------

Dual Memory System
~~~~~~~~~~~~~~~~~~

.. mermaid::

   graph TB
       subgraph "Short-Term Memory"
           ST1[Message N-19]
           ST2[Message N-18]
           ST3[...]
           ST4[Message N]
           
           ST1 --> ST2 --> ST3 --> ST4
       end
       
       subgraph "Long-Term Memory"
           subgraph "Summaries"
               S1[Summary 1<br/>Week old]
               S2[Summary 2<br/>Day old]
               S3[Summary 3<br/>Hour old]
           end
           
           subgraph "Notable Messages"
               N1[Message A<br/>with explanation]
               N2[Message B<br/>with explanation]
           end
       end
       
       ST4 -.->|Every 20 msgs| S3
       ST4 -.->|Notable| N2

Short-Term Memory
~~~~~~~~~~~~~~~~~

**Implementation:** ``memory.py``

* **Data Structure:** ``dict[int, deque]`` - chat_id → message deque
* **Capacity:** 20 messages per chat (configurable via ``MAX_MESSAGES``)
* **Storage:** In-memory only (lost on restart)
* **Use Case:** Immediate context for explanations

**Message Entry:**

.. code-block:: python

   {
       "user": "username",
       "text": "message text",
       "timestamp": "2026-02-14T10:00:00Z",
       "message_id": 12345
   }

Long-Term Memory
~~~~~~~~~~~~~~~~

**Implementation:** ``long_memory.py``

* **Storage:** JSON files in ``data/chats/{chat_id}.json``
* **Capacity:** 50 summaries, 100 notable messages per chat
* **Persistence:** Survives bot restarts
* **Use Case:** Historical context and learning

**Summary Entry:**

.. code-block:: json

   {
     "timestamp": "2026-02-14T10:00:00Z",
     "summary": "Group discussed weekend plans",
     "key_terms": ["macha", "scene"],
     "participants": ["Alice", "Bob"]
   }

**Notable Message Entry:**

.. code-block:: json

   {
     "timestamp": "2026-02-14T10:05:00Z",
     "user": "Rahul",
     "text": "Ayyo, don't put scene da",
     "explanation": "Don't create drama/excuses",
     "language_mix": "Kanglish"
   }

Intelligent Retrieval
~~~~~~~~~~~~~~~~~~~~~

**Implementation:** ``memory_retriever.py``

Instead of dumping all memory, BhashaBridge uses **keyword + recency scoring**:

1. **Extract Keywords:** Remove stopwords from target message
2. **Score Summaries:**
   * Keyword overlap: ``count(matching_terms) / total_terms``
   * Recency: ``1.0 / (1 + days_since)``
   * Combined: ``0.7 * keyword_score + 0.3 * recency_score``
3. **Filter:** Only keep summaries with score > 0.1
4. **Rank:** Return top 3 summaries
5. **Notable Messages:** Simple substring match

This ensures only relevant context is injected into prompts, keeping
responses focused and reducing token usage.

AI Engine Architecture
----------------------

**Implementation:** ``ai_engine.py``

The AI engine provides a unified interface to Google Gemini API with
specialized prompts for different use cases.

Unified Analysis
~~~~~~~~~~~~~~~~

The ``analyze_message()`` function is the primary entry point, making a
single API call that returns all needed information:

* Language detection
* Translation to English
* Vibe/tone analysis
* Slang glossary
* Translations to Hindi/Kannada
* Suggested replies (multiple tones)

This approach minimizes API calls and latency.

Specialized Functions
~~~~~~~~~~~~~~~~~~~~~

For cases requiring specific behavior:

* ``explain_message()`` - Human-readable explanation
* ``explain_with_translate()`` - Explanation in target language
* ``generate_reply()`` - Context-aware reply generation
* ``translate_message()`` - Direct translation
* ``summarize_conversation()`` - Create long-term memory entries
* ``detect_tone()`` - Single-word tone detection

Prompt Engineering
~~~~~~~~~~~~~~~~~~

All prompts follow these principles:

1. **Context First** - Long-term and recent context at the beginning
2. **Clear Instructions** - Explicit task descriptions
3. **Structured Output** - JSON schemas for machine parsing
4. **Error Handling** - Fallback responses for all functions
5. **Cultural Context** - Emphasis on Indian code-mixed nuances

Telegram Bot Architecture
-------------------------

**Implementation:** ``main.py``

Handler Registration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   application.add_handler(CommandHandler("start", start_command))
   application.add_handler(CommandHandler("clear", clear_command))
   application.add_handler(CommandHandler("setlang", setlang_command))
   application.add_handler(CommandHandler("settone", settone_command))
   application.add_handler(MessageHandler(filters, text_listener))
   application.add_handler(InlineQueryHandler(inline_handler))

Inline Mode Design
~~~~~~~~~~~~~~~~~~

The bot uses **inline mode** for privacy:

* Users type ``@BotName command args``
* Bot returns suggestions privately
* Only the user sees results until they select one
* Other group members see nothing

User Context Mapping
~~~~~~~~~~~~~~~~~~~~

Since inline queries don't include ``chat_id``, the bot maintains a mapping:

.. code-block:: python

   user_last_chat: dict[int, int] = {}  # user_id -> chat_id

Updated on every group message:

.. code-block:: python

   user_last_chat[update.effective_user.id] = update.effective_chat.id

Auto-Summarization
~~~~~~~~~~~~~~~~~~

Every 20 messages per chat:

1. Retrieve recent message history
2. Call ``ai_engine.summarize_conversation()``
3. Extract participants from messages
4. Save to long-term memory via ``long_memory.add_summary()``

This creates a feedback loop where the bot continuously learns from
conversations.

Security Considerations
-----------------------

Data Privacy
~~~~~~~~~~~~

* **Local Storage:** All memory stored locally in ``data/`` directory
* **No Cloud:** No data sent to third parties except Gemini API
* **User Control:** ``/clear`` command removes all user data
* **Encrypted Transport:** Telegram uses MTProto encryption

API Keys
~~~~~~~~

* Stored in environment variables (``.env``)
* Never committed to version control
* Separate keys for Telegram and Gemini

Input Sanitization
~~~~~~~~~~~~~~~~~~

* All user input passed through Telegram's API
* No direct database queries from user input
* JSON parsing wrapped in try/except blocks

Performance Optimizations
-------------------------

Memory Efficiency
~~~~~~~~~~~~~~~~~

* Deques with max length prevent unbounded growth
* Long-term memory limited to 50 summaries + 100 messages
* JSON files loaded only when needed

API Efficiency
~~~~~~~~~~~~~~

* ``analyze_message()`` returns all data in one call
* ``cache_time=0`` for inline queries prevents stale data
* Intelligent retrieval reduces prompt size

Concurrent Handling
~~~~~~~~~~~~~~~~~~~

* ``python-telegram-bot`` handles concurrency via asyncio
* Memory operations are thread-safe (dict operations)
* No locks required for read-heavy workloads

Scalability Considerations
--------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

* Single-process architecture
* In-memory short-term storage
* File-based long-term storage
* One bot instance per Telegram token

Future Improvements
~~~~~~~~~~~~~~~~~~~

* Redis for distributed memory
* Database backend (PostgreSQL/MongoDB)
* Microservices architecture
* Horizontal scaling with load balancer

Technology Stack
----------------

Core Technologies
~~~~~~~~~~~~~~~~~

* **Python 3.10+** - Modern Python with type hints
* **python-telegram-bot 20.7+** - Telegram Bot API wrapper
* **google-generativeai 0.8+** - Gemini API client
* **python-dotenv** - Environment variable management

Development Tools
~~~~~~~~~~~~~~~~~

* **pytest** - Testing framework
* **pytest-asyncio** - Async test support
* **pytest-cov** - Coverage reporting
* **ruff** - Linting and formatting

Documentation Tools
~~~~~~~~~~~~~~~~~~~

* **Sphinx** - Documentation generator
* **sphinx-rtd-theme** - ReadTheDocs theme
* **sphinxcontrib-mermaid** - Diagram support

Deployment
~~~~~~~~~~

* **uv** - Fast Python package manager
* **venv** - Virtual environment isolation

Design Patterns
---------------

Module Pattern
~~~~~~~~~~~~~~

Each module is self-contained with:

* Clear public API (documented functions)
* Private helpers (underscore prefix)
* No circular dependencies
* Standard library only (except where needed)

Factory Pattern
~~~~~~~~~~~~~~~

Model instantiation in ``ai_engine.py``:

.. code-block:: python

   model = genai.GenerativeModel(
       MODEL_NAME,
       system_instruction=SYSTEM_PROMPT,
   )

Singleton Pattern
~~~~~~~~~~~~~~~~~

Module-level storage in ``memory.py``:

.. code-block:: python

   chat_store: dict[int, deque] = {}

Repository Pattern
~~~~~~~~~~~~~~~~~~

Data access abstraction in ``long_memory.py``:

.. code-block:: python

   def load_chat_memory(chat_id: int) -> dict: ...
   def save_chat_memory(chat_id: int, data: dict) -> None: ...

Command Pattern
~~~~~~~~~~~~~~~

Handler structure in ``main.py``:

.. code-block:: python

   async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...
   async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...

Monitoring and Debugging
------------------------

Logging
~~~~~~~

Structured logging at INFO level:

.. code-block:: python

   logging.basicConfig(
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       level=logging.INFO,
   )

Error Handling
~~~~~~~~~~~~~~

All API calls wrapped in try/except with fallback responses.

Debugging Tips
~~~~~~~~~~~~~~

1. Check ``data/chats/`` for stored memories
2. Enable DEBUG logging for verbose output
3. Use ``pytest -v`` for detailed test output
4. Check Telegram Bot API logs for webhook issues

Future Enhancements
-------------------

Potential Improvements
~~~~~~~~~~~~~~~~~~~~~

* **Web Interface** - Admin dashboard for memory management
* **Analytics** - Usage statistics and popular terms
* **Custom Models** - Fine-tuned models for specific dialects
* **Voice Support** - Audio message translation
* **Multi-Bot** - Support for multiple bot instances
* **Plugin System** - Extensible architecture for new features
* **A/B Testing** - Experiment with different prompts
* **Feedback Loop** - User ratings for explanations

Architecture Decision Records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ADR-001: Why Inline Mode?
   * Privacy: Other users don't see interactions
   * Clean: No spam in group chat
   * Flexible: Works in any chat, not just groups

ADR-002: Why Dual Memory?
   * Performance: Fast access to recent context
   * Persistence: Learning survives restarts
   * Relevance: Smart retrieval keeps prompts focused

ADR-003: Why Gemini?
   * Multilingual: Excellent Indian language support
   * Context Window: Large context for conversation history
   * Speed: Fast enough for real-time interactions
   * Cost: Competitive pricing for hackathon budget
