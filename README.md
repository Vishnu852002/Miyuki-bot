# miyuki-bot 🤖

yo so i built this twitter bot that posts anime/gaming/tech stuff automatically. uses newsapi to get real headlines, then asks ollama to comment on them. runs locally (no api costs, if u have money go nuts)

## what it does

- fetches real news from NewsAPI and comments on them
- generates tweets using local LLM (ollama) - no paying for openai/google cloud api
- can post to twitter if you have api keys, otherwise just simulates
- remembers what it posted so it doesnt repeat itself
- has a monthly post limit so you dont go crazy
- can attach random images from a folder
- personality modes - make it chill, hyped, or go full shitpost mode
- quiet hours - wont post when ur asleep
- hashtag support

## setup

1. copy the env template and fill in your keys:
```bash
cp .env.example .env
# edit .env with your NEWSAPI_KEY and optionally twitter keys
```

2. install deps:
```bash
pip install -r requirements.txt
```

3. make sure ollama is running (I suggest using deepseek-r1 or anyother thinking model, only if u have a good pc with huge vram, ram and good cpu):
```bash
ollama run gemma3:4B
```

## env vars

check `.env.example` for all options. the main ones:

```bash
# required for real news
NEWSAPI_KEY=your_key_here  # get one at newsapi.org

# twitter (optional - leave blank for simulation mode)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=

# personality
PERSONALITY_MODE=chill    # options: chill, hyped, shitpost
USE_HASHTAGS=true

# testing without real news
SIMULATION_MODE=false     # set to true to allow creative prompts (testing only)
```

### personality modes

- **chill** (default): relaxed, casual, lowercase vibes. just hangin out
- **hyped**: ENERGY!! emojis, caps, excitement. for when u want engagement
- **shitpost**: chaotic. weird grammar. ironic. use at ur own risk

## running

```bash
python bot.py
```

thats it. it runs forever posting every 30 min (or whatever interval u set)

you should see something like:
```
miyuki-bot v1.1.0 starting up!
personality: chill | interval: 1800s | hashtags: True
quiet hours: 2:00 - 7:00
health check: ollama=ok twitter=simulation mode
```

## how it works

the bot:
1. picks a random category (anime/gaming/tech)
2. fetches real news headlines from NewsAPI
3. asks ollama to comment on a headline
4. checks if its too similar to recent posts (to avoid spam)
5. maybe adds a hashtag (40% chance if enabled)
6. posts to twitter or just logs it (simulation mode)
7. saves everything so it can remember what its already said
8. sleeps until next cycle

> note: if no news is available and SIMULATION_MODE is off, it skips posting (no fake news)

## files it creates

- `tweet_memory_*.json` - remembers past posts to avoid repeats
- `bot_analytics.json` - basic stats on what its posting
- `monthly_count.json` - tracks posts per month for limits

## todo

- [x] newsapi integration
- [ ] add scheduling (post at specific times of day)
- [ ] thread support (multi-tweet threads, paid api?)
- [ ] reply to mentions (paid api)
- [ ] will add duckduckgo search (ddgs) for more freshness...

## faq

**q: why ollama?**
a: free, runs locally, no api keys needed, privacy

**q: is this against twitter tos?**
a: probably check that yourself tbh. automation rules exist

**q: its posting cringe**
a: try a different model or personality mode. or embrace the cringe idk

## contributing

feel free to pr or open issues, im not super active but ill try to review stuff

see [CONTRIBUTING.md](CONTRIBUTING.md) if u want guidelines (theyre pretty chill)

---

MIT license, do whatever u want with it
