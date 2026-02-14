Usage Guide
===========

Complete guide to using BhashaBridge effectively.

Inline Mode Commands
--------------------

BhashaBridge operates primarily in **inline mode** for privacy. Type commands
anywhere in Telegram by starting with ``@YourBotName``.

Explain Command
~~~~~~~~~~~~~~~

Decode code-mixed messages with cultural context.

**Syntax:**

.. code-block:: text

   @YourBotName explain <message>

**Example:**

.. code-block:: text

   @YourBotName explain macha don't put scene da

**Output:**

* 🗣️ **Translation:** Literal English meaning
* 🎭 **Vibe Check:** Cultural context (sarcasm, affection, etc.)
* 📖 **Slang Glossary:** Definitions of code-mixed terms

Explain + Translate Command
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get explanations delivered in your preferred language.

**Syntax:**

.. code-block:: text

   @YourBotName explaintranslate <language> <message>

**Supported Languages:**

* ``hindi`` - Hindi
* ``kannada`` - Kannada
* ``english`` - English

**Example:**

.. code-block:: text

   @YourBotName explaintranslate hindi macha don't put scene

Reply Command
~~~~~~~~~~~~~

Generate contextually appropriate replies.

**Syntax:**

.. code-block:: text

   @YourBotName reply [tone] <message>

**Without tone:** Auto-detects tone from context

.. code-block:: text

   @YourBotName reply macha come fast

**With tone:** Specify desired tone

.. code-block:: text

   @YourBotName reply formal macha come fast

**Available Tones:**

* ``casual`` - Friendly, relaxed
* ``formal`` - Professional, polite
* ``sarcastic`` - Playful mockery
* ``funny`` - Humorous
* ``angry`` - Frustrated
* ``polite`` - Respectful
* ``friendly`` - Warm
* ``professional`` - Business-like
* ``flirty`` - Playful romantic
* ``chill`` - Relaxed
* ``playful`` - Fun-loving
* ``affectionate`` - Warm and caring
* ``frustrated`` - Annoyed
* ``humorous`` - Joking
* ``urgent`` - Time-sensitive

Translate Command
~~~~~~~~~~~~~~~~~

Translate messages between supported languages.

**Syntax:**

.. code-block:: text

   @YourBotName translate <language> <text>

**Example:**

.. code-block:: text

   @YourBotName translate kannada I'll be there in 10 minutes

Slash Commands (DM Only)
------------------------

These commands work in private chat with the bot.

/start
~~~~~~

Display welcome message and usage instructions.

/clear
~~~~~~

Clear all memory (both short-term and long-term) for your account.

**Use case:** Reset the bot if it learns incorrect patterns.

/setlang
~~~~~~~~

Set your default language preference.

**Syntax:**

.. code-block:: text

   /setlang <language>

**Example:**

.. code-block:: text

   /setlang hindi

/settone
~~~~~~~~

Set your default reply tone preference.

**Syntax:**

.. code-block:: text

   /settone <tone>

**Example:**

.. code-block:: text

   /settone casual

**To clear:** Use without arguments

.. code-block:: text

   /settone

How It Works
------------

Memory System
~~~~~~~~~~~~~

BhashaBridge uses a **dual memory system**:

**Short-Term Memory (Sliding Window)**

* Stores last 20 messages per chat
* In-memory only (fast access)
* Lost on bot restart

**Long-Term Memory (Persistent)**

* Stores conversation summaries and notable messages
* JSON files in ``data/`` directory
* Survives bot restarts

**Auto-Summarization**

Every 20 messages, the bot automatically creates a summary and stores it
in long-term memory. This allows the bot to maintain context across days
or even weeks.

Intelligent Retrieval
~~~~~~~~~~~~~~~~~~~~~

Instead of dumping all memory into prompts, BhashaBridge uses **smart retrieval**:

1. Extracts keywords from the target message
2. Scores summaries by keyword overlap + recency
3. Returns only the top 3 most relevant summaries
4. Matches notable messages by substring

This keeps prompts lean and focused, improving response quality.

Context Awareness
~~~~~~~~~~~~~~~~~

The bot maintains a mapping of ``user_id → chat_id`` based on recent messages.
This allows inline queries to access the correct chat context even though
inline queries don't include chat_id information.

**Important:** You must send at least one regular message in a group before
using inline mode in that group.

Best Practices
--------------

For Group Admins
~~~~~~~~~~~~~~~~

1. **Disable Privacy Mode**
   * Required for the bot to read all messages
   * Do this in @BotFather

2. **Set Clear Expectations**
   * Let users know the bot silently listens
   * Explain that inline mode keeps interactions private

3. **Monitor Usage**
   * Check ``data/chats/`` directory for storage usage
   * Use ``/clear`` if memory gets too large

For Users
~~~~~~~~~

1. **Start Simple**
   * Try the ``explain`` command first
   * Use ``reply`` when you want response suggestions

2. **Set Preferences**
   * Use ``/setlang`` to get explanations in your language
   * Use ``/settone`` for consistent reply style

3. **Provide Context**
   * The bot works best with conversation history
   * Send a few messages before using inline mode

4. **Iterate**
   * If a reply doesn't fit, try a different tone
   * Use ``explaintranslate`` for better understanding

Language Support
----------------

Supported Code-Mixed Languages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Hinglish** - Hindi + English
* **Kanglish** - Kannada + English
* **Tanglish** - Tamil + English
* **Tenglish** - Telugu + English

The bot automatically detects the language mix from context.

Supported Output Languages
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **English** - Default
* **Hindi** - Full explanations and translations
* **Kannada** - Full explanations and translations

Examples
--------

Kanglish Examples
~~~~~~~~~~~~~~~~~

**Input:**

.. code-block:: text

   @YourBotName explain macha don't put scene da

**Output:**

* **Translation:** "Bro, don't create drama/excuses"
* **Vibe:** Casual warning among friends
* **Slang:**
  * macha - "bro/friend" (Kannada influence)
  * scene - "drama/situation"
  * da - casual particle (Kannada)

**Input:**

.. code-block:: text

   @YourBotName reply casual ayyo sumne iru

**Output:** Suggested casual reply to "Just be quiet/leave it"

Hinglish Examples
~~~~~~~~~~~~~~~~~

**Input:**

.. code-block:: text

   @YourBotName explain kya scene hai bhai

**Output:**

* **Translation:** "What's the situation/scene, brother?"
* **Vibe:** Casual inquiry about what's happening

**Input:**

.. code-block:: text

   @YourBotName translate hindi See you tomorrow

**Output:** "Kal milte hain"

Troubleshooting Common Issues
------------------------------

"No Chat Context" Error
~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** The bot doesn't know which chat you're referring to.

**Solution:**

1. Send a regular message in the group
2. Wait a moment for the bot to process
3. Try your inline command again

Bot Not Responding
~~~~~~~~~~~~~~~~~~

**Checklist:**

1. Is the bot running? (Check terminal output)
2. Is inline mode enabled? (Check @BotFather)
3. Is privacy mode disabled? (Check @BotFather)
4. Are environment variables set correctly?

Poor Explanations
~~~~~~~~~~~~~~~~~

**Causes:**

* Very short or unclear messages
* Regional slang not in training data
* Missing context

**Solutions:**

* Provide more context in the message
* Use the full conversation as input
* Set your preferred language with ``/setlang``

Slow Responses
~~~~~~~~~~~~~~

**Causes:**

* Gemini API latency
* Complex conversation context
* Rate limiting

**Solutions:**

* Be patient (usually 1-3 seconds)
* Consider upgrading Gemini API tier
* Check your internet connection

Advanced Usage
--------------

Custom Tones
~~~~~~~~~~~~

You can use any descriptive word for tone:

.. code-block:: text

   @YourBotName reply enthusiastic Party tonight!
   @YourBotName reply diplomatic Can we reschedule?
   @YourBotName reply empathetic I'm so sorry to hear that

The bot will interpret the tone and generate an appropriate response.

Batch Translation
~~~~~~~~~~~~~~~~~

While not officially supported, you can chain translations:

.. code-block:: text

   @YourBotName translate hindi Hello
   @YourBotName translate kannada Hello
   @YourBotName translate english Namaste

Privacy Considerations
~~~~~~~~~~~~~~~~~~~~~~

* Short-term memory is cleared on restart
* Long-term data is stored locally in ``data/``
* No data is sent to Telegram except replies
* Gemini API processes messages for understanding

To completely clear your data, use ``/clear`` in DM with the bot.
