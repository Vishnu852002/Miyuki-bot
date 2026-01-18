# miyuki-bot

An automated Twitter/X bot that posts anime, gaming, and tech commentary using real news headlines and a locally running LLM.

Built as a personal side project to explore automation, prompt control, and local inference without relying on paid APIs.

---

## Overview

miyuki-bot periodically fetches real headlines from NewsAPI, generates short commentary using Ollama, and posts them to Twitter/X (or runs in simulation mode).

Designed to be cheap, local-first, and predictable. No cloud LLM costs. No hidden magic. Just a script that does its job.

---

## Features

- Pulls real headlines from NewsAPI  
- Generates posts using a local LLM via Ollama  
- Optional Twitter/X posting, or simulation-only mode  
- Avoids duplicate or near-duplicate posts  
- Monthly post limit to prevent spam  
- Supports quiet hours  
- Optional hashtag injection  
- Random image attachment from a local folder  
- Simple personality modes for tone control  

---

## Non-Goals

- No replies to mentions  
- No thread generation  
- No engagement farming logic  

These are intentionally excluded due to API limits and added complexity.

---

## Setup

### 1. Environment variables

Copy the template and add your keys:

```bash
cp .env.example .env
```

**Required:**
- `NEWSAPI_KEY`

**Optional:**
- Twitter/X API keys for live posting

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Ollama

Make sure Ollama is running locally. Any compatible model works.

```bash
ollama run gemma3:4B
```

Heavier reasoning models will require more RAM and VRAM.

---

## Configuration

Key options in `.env`:

```bash
PERSONALITY_MODE=chill   # chill | hyped | shitpost
USE_HASHTAGS=true
SIMULATION_MODE=false
```

Personality modes only affect tone, not behavior.

---

## Running the bot

```bash
python bot.py
```

The bot runs continuously and posts at a fixed interval.

Example startup output:

```
miyuki-bot v1.1.1 starting
personality: chill | interval: 1800s
quiet hours: 02:00 - 07:00
twitter: simulation mode
ollama: connected
```

---

## How it works

1. Selects a random topic category
2. Fetches recent headlines from NewsAPI
3. Generates commentary using Ollama
4. Filters out similar past posts
5. Optionally adds a hashtag
6. Posts or logs the result
7. Saves state locally
8. Sleeps until the next cycle

If no valid news is available, it skips posting.

---

## Generated files

| File | Purpose |
|------|---------|
| `tweet_memory_*.json` | Tracks previous posts to avoid repetition |
| `monthly_count.json` | Enforces posting limits |
| `bot_analytics.json` | Basic posting statistics |

---

## Roadmap

- [ ] Scheduled posting times
- [ ] Thread support
- [ ] Mentions and replies
- [ ] Additional news sources (DuckDuckGo search)

---

## License

MIT License.  
Use it, modify it, break it. Just don't blame me.