# Miyuki-Bot

Miyuki-Bot is a professional, privacy-safe automated content generator and poster.  
It uses a local Ollama LLM backend for text generation and optionally integrates with Twitter via Tweepy.

---

## Features
- Local LLM generation with Ollama (no cloud dependency)
- Optional Twitter posting via OAuth1
- Simulation mode when no credentials are provided
- Memory system to avoid repeated posts
- Automatic monthly posting limits
- Clean logging and modular architecture
- Fully environment-variable configurable

---

## Requirements

Install dependencies with:

```
pip install -r requirements.txt
```

---

## Environment Variables

Set these before running the bot.

### Ollama
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4B  # Any Ollama-supported model can be used
```

### Optional: Twitter (real posting)
```
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
```

### Optional: News API
```
NEWSAPI_KEY=
```

### Optional: Advanced config
```
POST_INTERVAL_SECONDS=1800
MAX_POSTS_PER_MONTH=500
IMAGE_FOLDER=./images
```

---

## Usage

Start Ollama locally:

```
ollama run gemma3:4B
```

Run the bot:

```
python newsbot_clean.py
```

The bot will run indefinitely, posting at the configured interval.

---

## Folder Structure

```
/repo
 ├── newsbot_clean.py
 ├── README.md
 ├── requirements.txt
 ├── images/
 └── tweet_memory_*.json
```

---

## Notes
- Without Twitter credentials, the bot runs in simulation mode.  
- Memory files prevent repeating similar content.  
- Optional analytics are automatically saved.

---

## License
MIT License.  
Feel free to fork, modify, and contribute.
