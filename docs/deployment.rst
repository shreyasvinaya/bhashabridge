Local Deployment Guide
======================

Complete guide for deploying BhashaBridge locally.

Prerequisites
-------------

System Requirements
~~~~~~~~~~~~~~~~~~~

* **OS:** Linux, macOS, or Windows with WSL
* **Python:** 3.10 or higher
* **RAM:** 512 MB minimum (2 GB recommended)
* **Disk:** 100 MB for code + data storage
* **Network:** Stable internet connection

Required Accounts
~~~~~~~~~~~~~~~~~

1. **Telegram Account** - For creating bot via @BotFather
2. **Google Account** - For Gemini API access

Installation Steps
------------------

Step 1: Clone Repository
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone <your-repository-url>
   cd bhashabridge

Step 2: Install uv
~~~~~~~~~~~~~~~~~~

If you don't have uv installed:

.. code-block:: bash

   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

Step 3: Create Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uv venv .venv

Step 4: Activate Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Linux/macOS:**

.. code-block:: bash

   source .venv/bin/activate

**Windows:**

.. code-block:: bash

   .venv\Scripts\activate

Step 5: Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uv pip install -e ".[dev]"

Configuration
-------------

Step 1: Create Environment File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cp .env.example .env

Step 2: Get Telegram Bot Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open Telegram and message @BotFather
2. Send /newbot command
3. Follow prompts to name your bot
4. Save the token provided by BotFather
5. Edit .env and add your token

Step 3: Get Gemini API Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Visit Google AI Studio
2. Sign in with your Google account
3. Click Create API Key
4. Copy the key and add to .env

Step 4: Configure Bot Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Telegram, message @BotFather and enable inline mode, disable privacy mode.

Running the Bot
---------------

Development Mode
~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py

You should see: BhashaBridge is live!

Testing
-------

Run Unit Tests
~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/ -v

Manual Testing
~~~~~~~~~~~~~~~

1. Add bot to a test group
2. Send messages in code-mixed language
3. Use inline commands to test

Monitoring
----------

Check bot is running:

.. code-block:: bash

   ps aux | grep python

View logs in terminal or bot.log file.

Maintenance
-----------

Update dependencies:

.. code-block:: bash

   uv pip install -e ".[dev]"

Clear data:

.. code-block:: bash

   rm -rf data/
   # Or use /clear command in DM

Backup data:

.. code-block:: bash

   tar -czf backup-$(date +%Y%m%d).tar.gz data/
