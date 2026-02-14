# 🌉 BhashaBridge
> **Don't just translate words. Understand the vibe.**

[![Gemini 3.0 Flash](https://img.shields.io/badge/Powered%20By-Gemini%202.0%20Flash-blue)](https://deepmind.google/technologies/gemini/)
[![Telegram](https://img.shields.io/badge/Platform-Telegram%20Inline-2CA5E0)](https://telegram.org/)
[![Hackathon](https://img.shields.io/badge/Event-Gemini%203%20Bengaluru-orange)](https://ai.google.dev/)

---

## 🚀 The Problem
In a diverse country like India, nobody speaks just "English" or "Hindi". We speak **code-mixed** languages:
> *"Ayyo macha, don't put scene da, just send the code na."*

Standard translators fail here. They can translate the words, but they miss:
1.  **The "Vibe"**: Is the user angry? Joking? Frustrated?
2.  **The Slang**: What does "put scene" mean? (It means creating drama/excuses).
3.  **The Context**: Who is speaking to whom?

## 💡 The Solution: BhashaBridge
BhashaBridge is an **invisible, context-aware AI companion** that lives in your chat app. It doesn't just translate; it **culturalizes**.

Using **Google's Gemini 3.0 Flash**, it analyzes live conversations to provide:
-   **🎭 Vibe Checks**: Detects if a message is sarcastic, formal, or casual.
-   **📖 Slang Glossaries**: Explains "Macha", "Jugaad", "Scene" in real-time.
-   **💬 Smart Replies**: Suggests responses that match the *tone* of the group.

---

## 💼 Real-World Use Cases

### 1. 🎧 Next-Gen Customer Support (Agent Assist)
**The Challenge**: Support agents often struggle with customers using hyper-local slang or mixed languages (Hinglish/Tanglish/Kanglish), leading to miscommunication and low CSAT scores.
**The BhashaBridge Fix**: 
-   **Sentiment + Vibe Analysis**: "Sir, thoda adjust maadi" isn't just a request; it's a polite plea for flexibility. BhashaBridge tells the agent *exactly* how the customer feels.
-   **Tone-Matching Replies**: Suggests replies that build rapport. If the customer is casual, the agent shouldn't sound like a robot.
-   **Outcome**: Faster resolution, higher empathy, stronger customer connection.

### 2. 🏙️ The "New in Bengaluru" Survival Tool
**The Challenge**: You just moved to Bangalore (or Delhi/Chennai/Hyderabad). Your society WhatsApp group is buzzing with text you can't read or slang you don't get.
**The BhashaBridge Fix**: 
-   **Invisible Explainer**: Without looking like a novice by asking "What does this mean?", you can use BhashaBridge in **inline mode** to privately decode messages.
-   **Outcome**: Seamless social integration and zero "culture shock".

### 3. 🤝 Inclusive Enterprise Communication
**The Challenge**: Pan-India teams often have communication gaps. A joke made in a regional mix might be misunderstood as rude by a colleague from another state.
**The BhashaBridge Fix**: Acts as a cultural bridge, explaining intent and ensuring humor/sarcasm translates correctly across regions.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **👻 Invisible Mode** | Works via Telegram **Inline Queries**. You don't need to add the bot to the group to use it. Your "dumb questions" remain private. |
| **🧠 Context Awareness** | Remembers the last 20 messages to understand *flow*. It knows if "Right" means "Correct" or "You are annoying" based on chat history. |
| **⚡ Smart Auto-Reply** | Generates replies (Casual, Formal, Sarcastic) that match the code-mixed language style of the sender. |
| **🌐 Multi-Lingual** | Native support for **Hinglish** (Hindi+Eng), **Kanglish** (Kannada+Eng), **Tanglish**, and more. |

---

## 🛠️ Tech Stack

-   **LLM**: **Google Gemini 3.0 Flash** (via `google-genai` SDK) for lightning-fast token generation and nuanced cultural understanding.
-   **Platform**: **Telegram Bot API** (Python) utilizing `InlineQueryResultArticle` for private interaction.
-   **Memory**: 
    -   *Short-term*: In-memory sliding window deque.
    -   *Long-term*: JSON-based persistent storage with **Smart Retrieval** (Keyterm match + Recency scoring) to feed relevant context to Gemini.
-   **Language**: Python 3.10+

---

## ⚡ Quick Start

### 1. Prerequisites
1.  **Telegram Bot Token**: Get one from [@BotFather](https://t.me/BotFather).
    -   Enable Inline Mode: `/setinline` -> `Type to explain...`
    -   Disable Privacy: `/setprivacy` -> `Disable` (allows bot to read group context if added).
2.  **Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/shreyasvinaya/bhashabridge.git
cd bhashabridge

# create a virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Run to Bridge
```bash
python main.py
```

---

> Built with ❤️ at Gemini 3 Bengaluru Hackathon
