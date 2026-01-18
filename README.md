# miyuki-bot 🤖

yo so i built this twitter bot that posts anime/gaming/tech stuff automatically. it uses ollama for generation so everything runs locally on your machine (no api costs, if u have money go nuts, interval can be reduced and newsapi give u latest news too.)

## what it does

- generates tweets using local LLM (ollama) - no paying for openai
- can post to twitter if you have api keys, otherwise just simulates
- remembers what it posted so it doesnt repeat itself
- has a monthly post limit so you dont go crazy
- can attach random images from a folder
- **NEW:** personality modes - make it chill, hyped, or go full shitpost mode
- **NEW:** quiet hours - wont post when ur asleep
- **NEW:** varied prompts - randomly picks different content styles

## setup

```bash
pip install -r requirements.txt
```

make sure ollama is running first:
```bash
ollama run gemma3:4B
```

## env vars

```bash
# required
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4B  # or whatever model u want

# optional - leave these blank to run in simulation mode (good for testing)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# personality stuff (this is the fun part)
PERSONALITY_MODE=chill    # options: chill, hyped, shitpost
USE_HASHTAGS=true         # set to false if u hate hashtags
QUIET_HOURS_START=2       # dont post between 2am and 7am
QUIET_HOURS_END=7

# other settings
NEWSAPI_KEY=              # if u want news integration
POST_INTERVAL_SECONDS=1800  # how often to post (default 30 min)
MAX_POSTS_PER_MONTH=500
IMAGE_FOLDER=./images     # put images here and itll randomly attach them
```

### personality modes

- **chill** (default): relaxed, casual, lowercase vibes. just hangin out
- **hyped**: ENERGY!! emojis, caps, excitement. for when u want engagement
- **shitpost**: chaotic. weird grammar. ironic. use at ur own risk lmao

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
2. picks a random prompt from that category
3. generates content using ollama with the personality mode
4. checks if its too similar to recent posts (to avoid spam)
5. maybe adds a hashtag (40% chance if enabled)
6. posts to twitter or just logs it (simulation mode)
7. saves everything so it can remember what its already said
8. sleeps until next cycle

## files it creates

- `tweet_memory_*.json` - remembers past posts to avoid repeats
- `bot_analytics.json` - basic stats on what its posting
- `monthly_count.json` - tracks posts per month for limits

## todo

- [ ] add scheduling (post at specific times of day)
- [ ] thread support (multi-tweet threads, I think it's paid?)
- [ ] reply to mentions maybe? (paid stuff on X API so i didnt go there...Although I could add it)
- [ ] different posting frequency by time of day (Easy to add, but i didn't find it interesting...)
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
