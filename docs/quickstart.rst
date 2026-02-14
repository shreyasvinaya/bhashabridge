Quickstart Guide
================

Get BhashaBridge running in 5 minutes.

Prerequisites
-------------

* Python 3.10 or higher
* Telegram Bot Token (from `@BotFather <https://t.me/BotFather>`_)
* Gemini API Key (from `Google AI Studio <https://aistudio.google.com/apikey>`_)

Installation
------------

1. Clone the repository:

   .. code-block:: bash

      git clone <repository-url>
      cd bhashabridge

2. Create virtual environment with uv:

   .. code-block:: bash

      uv venv .venv
      source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3. Install dependencies:

   .. code-block:: bash

      uv pip install -e ".[dev]"

Configuration
-------------

1. Copy the example environment file:

   .. code-block:: bash

      cp .env.example .env

2. Edit ``.env`` and add your credentials:

   .. code-block:: bash

      TELEGRAM_TOKEN=your_telegram_bot_token_here
      GEMINI_API_KEY=your_gemini_api_key_here

Setup Telegram Bot
------------------

1. Message `@BotFather <https://t.me/BotFather>`_ and create a new bot
2. Note down the bot token
3. Enable inline mode:

   * Send ``/setinline`` to @BotFather
   * Select your bot
   * Set placeholder: ``Type to explain, translate, or reply...``

4. Disable group privacy:

   * Send ``/setprivacy`` to @BotFather
   * Select your bot
   * Choose **Disable**

Running the Bot
---------------

Start the bot with:

.. code-block:: bash

   python main.py

You should see:

.. code-block:: text

   🌉 BhashaBridge is live!

Testing
-------

1. Add the bot to a Telegram group
2. Send a few messages (the bot silently listens)
3. Type ``@YourBotName explain macha don't put scene``
4. Select the result to see the explanation!

Next Steps
----------

* Read the full :doc:`usage` guide
* Learn about the :doc:`architecture`
* Check out the :doc:`api` reference
* See :doc:`deployment` for production tips

Troubleshooting
---------------

**Bot doesn't respond to inline queries**
   * Make sure inline mode is enabled in @BotFather
   * Check that the bot token is correct in ``.env``

**"No Chat Context" error**
   * Send a regular message in the group first
   * The bot needs to see your messages to establish context

**API errors**
   * Verify your Gemini API key is valid
   * Check that you have API quota available
