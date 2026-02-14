API Reference
=============

Complete API documentation for all BhashaBridge modules.

ai_engine Module
----------------

.. automodule:: ai_engine
   :members:
   :undoc-members:
   :show-inheritance:

   Core AI functionality integrating with Google Gemini API.

memory Module
-------------

.. automodule:: memory
   :members:
   :undoc-members:
   :show-inheritance:

   Short-term sliding window memory for recent messages.

long_memory Module
------------------

.. automodule:: long_memory
   :members:
   :undoc-members:
   :show-inheritance:

   Long-term persistent memory using JSON file storage.

memory_retriever Module
-----------------------

.. automodule:: memory_retriever
   :members:
   :undoc-members:
   :show-inheritance:

   Intelligent memory retrieval with keyword and recency scoring.

main Module
-----------

.. automodule:: main
   :members:
   :undoc-members:
   :show-inheritance:

   Telegram bot entry point and handler registration.

Function Reference
------------------

AI Engine Functions
~~~~~~~~~~~~~~~~~~~

analyze_message(recent_history, long_term_context, target_message)
   Perform comprehensive analysis of a message.
   
   :param recent_history: Formatted string of recent chat messages
   :param long_term_context: Relevant long-term memory context
   :param target_message: The message to analyze
   :returns: Dictionary with is_english, detected_language, translation, vibe, tone, slang, translations, suggested_replies

explain_message(recent_history, long_term_context, target_message)
   Explain a code-mixed message.
   
   :param recent_history: Formatted string of recent chat messages
   :param long_term_context: Relevant long-term memory context
   :param target_message: The message to explain
   :returns: Formatted explanation string or "NO_CONTEXT"

explain_with_translate(recent_history, long_term_context, target_message, target_language)
   Explain a message and deliver in target language.
   
   :param recent_history: Formatted string of recent chat messages
   :param long_term_context: Relevant long-term memory context
   :param target_message: The message to explain
   :param target_language: Language for explanation (hindi, kannada, english)
   :returns: Formatted explanation in target language

generate_reply(recent_history, long_term_context, target_message, tone, language)
   Generate a contextually appropriate reply.
   
   :param recent_history: Formatted string of recent chat messages
   :param long_term_context: Relevant long-term memory context
   :param target_message: The message to reply to
   :param tone: Desired tone (casual, formal, etc.)
   :param language: Target language for reply
   :returns: Generated reply text

translate_message(text, target_language)
   Translate text to target language.
   
   :param text: Text to translate
   :param target_language: Target language (hindi, kannada, english)
   :returns: Translated text

summarize_conversation(messages_text)
   Summarize a batch of messages.
   
   :param messages_text: Formatted conversation text
   :returns: Dictionary with summary, key_terms, participants

detect_tone(recent_history, target_message)
   Detect the tone/mood of a message.
   
   :param recent_history: Formatted string of recent chat messages
   :param target_message: The message to analyze
   :returns: Single word or short phrase describing tone

Memory Functions
~~~~~~~~~~~~~~~~

add_message(chat_id, user, text, message_id, timestamp=None)
   Add a message to short-term memory.
   
   :param chat_id: Unique chat identifier
   :param user: Username or display name
   :param text: Message text content
   :param message_id: Unique message identifier
   :param timestamp: Optional ISO 8601 timestamp (defaults to current UTC)

get_recent_messages(chat_id, n=10)
   Get the most recent n messages from a chat.
   
   :param chat_id: Unique chat identifier
   :param n: Number of messages to retrieve (default: 10)
   :returns: List of message dictionaries

get_history_text(chat_id, n=10)
   Get formatted chat history as text.
   
   :param chat_id: Unique chat identifier
   :param n: Number of messages to include (default: 10)
   :returns: Formatted string "user: text" per line

clear_history(chat_id)
   Clear all short-term memory for a chat.
   
   :param chat_id: Unique chat identifier

get_all_chat_ids()
   Get list of all chat IDs in memory.
   
   :returns: List of chat IDs

Long-Term Memory Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

load_chat_memory(chat_id)
   Load chat memory from persistent storage.
   
   :param chat_id: Unique chat identifier
   :returns: Dictionary with chat_id, summaries, notable_messages

save_chat_memory(chat_id, data)
   Save chat memory to persistent storage.
   
   :param chat_id: Unique chat identifier
   :param data: Dictionary with memory data

add_summary(chat_id, summary, key_terms, participants)
   Add a conversation summary.
   
   :param chat_id: Unique chat identifier
   :param summary: Text summary of conversation
   :param key_terms: List of slang/code-mixed terms
   :param participants: List of participant names

add_notable_message(chat_id, user, text, explanation, language_mix)
   Add a notable message.
   
   :param chat_id: Unique chat identifier
   :param user: Username of sender
   :param text: Original message text
   :param explanation: Explanation of meaning
   :param language_mix: Detected language mix (e.g., "Kanglish")

load_user_prefs(user_id)
   Load user preferences.
   
   :param user_id: Unique user identifier
   :returns: Dictionary with user_id, preferred_language, preferred_tone, interaction_count, last_used

save_user_prefs(user_id, prefs)
   Save user preferences.
   
   :param user_id: Unique user identifier
   :param prefs: Dictionary with preference data

update_user_prefs(user_id, language=None, tone=None)
   Update user preferences.
   
   :param user_id: Unique user identifier
   :param language: Optional new preferred language
   :param tone: Optional new preferred tone
   :returns: Updated preferences dictionary

clear_chat_memory(chat_id)
   Clear all long-term memory for a chat.
   
   :param chat_id: Unique chat identifier

clear_user_prefs(user_id)
   Clear user preferences.
   
   :param user_id: Unique user identifier

Memory Retriever Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

retrieve_relevant_context(chat_id, target_message)
   Retrieve relevant long-term context.
   
   :param chat_id: Unique chat identifier
   :param target_message: Message to find context for
   :returns: Formatted string with relevant summaries and notable messages

Constants
---------

ai_engine Module
~~~~~~~~~~~~~~~~

.. py:data:: MODEL_NAME
   
   Gemini model identifier. Default: ``"gemini-2.0-flash"``

.. py:data:: SYSTEM_PROMPT
   
   System prompt used for all AI interactions.

memory Module
~~~~~~~~~~~~~

.. py:data:: MAX_MESSAGES
   
   Maximum messages per chat in short-term memory. Default: ``20``

long_memory Module
~~~~~~~~~~~~~~~~~~

.. py:data:: MAX_SUMMARIES
   
   Maximum summaries per chat. Default: ``50``

.. py:data:: MAX_NOTABLE_MESSAGES
   
   Maximum notable messages per chat. Default: ``100``

memory_retriever Module
~~~~~~~~~~~~~~~~~~~~~~~

.. py:data:: STOPWORDS
   
   Set of common English words excluded from keyword extraction.

.. py:data:: TOP_K_SUMMARIES
   
   Number of top summaries to retrieve. Default: ``3``

.. py:data:: MAX_NOTABLE_MESSAGES
   
   Maximum notable messages to include. Default: ``5``

.. py:data:: MIN_SCORE_THRESHOLD
   
   Minimum relevance score for inclusion. Default: ``0.1``

main Module
~~~~~~~~~~~

.. py:data:: SUPPORTED_LANGUAGES
   
   Dictionary mapping language codes to display names.

.. py:data:: SUMMARY_TRIGGER
   
   Messages between auto-summarization. Default: ``20``

.. py:data:: RECOGNIZED_TONES
   
   Set of recognized tone keywords.

Type Hints
----------

Common Type Aliases
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Message entry in short-term memory
   MessageEntry = dict[str, Union[str, int]]
   
   # Summary entry in long-term memory
   SummaryEntry = dict[str, Union[str, list[str]]]
   
   # Notable message entry
   NotableEntry = dict[str, str]
   
   # User preferences
   UserPrefs = dict[str, Union[int, str, None]]
   
   # Analysis result
   AnalysisResult = dict[str, Union[bool, str, dict]]

Exception Handling
------------------

All functions in BhashaBridge follow defensive programming practices:

* **API Failures:** Return sensible defaults (empty dicts/strings)
* **Missing Data:** Create default structures on-the-fly
* **Invalid Input:** Validate and return error messages
* **File Errors:** Handle corrupted JSON gracefully

Example error handling pattern:

.. code-block:: python

   try:
       result = some_api_call()
       return result
   except Exception:
       logger.error("API call failed")
       return DEFAULT_FALLBACK

Best Practices
--------------

Using the AI Engine
~~~~~~~~~~~~~~~~~~~~

1. **Prefer analyze_message():** Makes a single API call for all data
2. **Cache results:** Don't call API multiple times for same message
3. **Handle fallbacks:** Always check for API error responses
4. **Provide context:** Pass recent_history and long_term_context

Using Memory
~~~~~~~~~~~~

1. **Don't bypass retrieval:** Use memory_retriever instead of direct access
2. **Clear when needed:** Use clear_history() for fresh starts
3. **Monitor storage:** Check data/ directory size periodically
4. **Backup data:** Copy data/ directory before major updates

Extending the Bot
~~~~~~~~~~~~~~~~~

1. **New commands:** Add CommandHandler in main.py
2. **New AI features:** Add function in ai_engine.py
3. **New storage:** Extend long_memory.py
4. **Always test:** Add tests in tests/ directory

Examples
--------

Basic Usage
~~~~~~~~~~~~

.. code-block:: python

   from ai_engine import analyze_message
   from memory import get_history_text
   from memory_retriever import retrieve_relevant_context
   
   chat_id = 123456
   target = "macha don't put scene"
   
   # Get context
   recent = get_history_text(chat_id, n=10)
   long_term = retrieve_relevant_context(chat_id, target)
   
   # Analyze
   result = analyze_message(recent, long_term, target)
   
   print(f"Translation: {result['translation']}")
   print(f"Tone: {result['tone']}")

Advanced Usage
~~~~~~~~~~~~~~~

.. code-block:: python

   from long_memory import add_summary, add_notable_message
   from ai_engine import summarize_conversation
   from memory import get_history_text
   
   # Summarize conversation
   chat_id = 123456
   history = get_history_text(chat_id, n=20)
   result = summarize_conversation(history)
   
   # Store summary
   add_summary(
       chat_id,
       result["summary"],
       result["key_terms"],
       result["participants"]
   )
   
   # Store notable message
   add_notable_message(
       chat_id,
       user="Alice",
       text="macha scene maadbeda",
       explanation="Don't create drama",
       language_mix="Kanglish"
   )
