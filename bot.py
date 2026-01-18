"""
miyuki-bot - a twitter bot that posts anime/gaming/tech stuff

basically just runs ollama locally, generates tweets, and posts them
if you dont have twitter keys it just simulates (prints to console)

quick start:
    pip install -r requirements.txt
    ollama run gemma3:4B  # or whatever model
    python bot.py

set TWITTER_* env vars if you want to actually post
"""
from __future__ import annotations

VERSION = "1.1.0"

import os
import sys
import json
import time
import logging
import random
import datetime
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests

# Optional dependency: tweepy
try:
    import tweepy
    TWEETY_AVAILABLE = True
except Exception:
    tweepy = None
    TWEETY_AVAILABLE = False

# --- Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4B")   # or whatever model u want. search on ollama.com/search for models
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Twitter credentials via env (leave empty to run in simulation mode)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

# Operational settings
POST_INTERVAL_SECONDS = int(os.getenv("POST_INTERVAL_SECONDS", str(30 * 60)))  # default 30 minutes
MAX_POSTS_PER_MONTH = int(os.getenv("MAX_POSTS_PER_MONTH", "500"))
COUNTER_FILE = Path(os.getenv("COUNTER_FILE", "monthly_count.json"))
MEMORY_DURATION_DAYS = int(os.getenv("MEMORY_DURATION_DAYS", "30"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.4"))
IMAGE_FOLDER = Path(os.getenv("IMAGE_FOLDER", "./images")).expanduser()
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", str(5 * 1024 * 1024)))
ANALYTICS_FILE = Path(os.getenv("ANALYTICS_FILE", "bot_analytics.json"))
MEMORY_FILES = {
    "news": Path("tweet_memory_news.json"),
    "facts": Path("tweet_memory_facts.json"),
    "questions": Path("tweet_memory_questions.json"),
}
CACHE_DURATION = int(os.getenv("CACHE_DURATION", str(60 * 60)))  # seconds

# personality & content settings
PERSONALITY_MODE = os.getenv("PERSONALITY_MODE", "chill")  # chill, hyped, shitpost
USE_HASHTAGS = os.getenv("USE_HASHTAGS", "true").lower() == "true"
QUIET_HOURS_START = int(os.getenv("QUIET_HOURS_START", "2"))  # hour to stop posting (24h)
QUIET_HOURS_END = int(os.getenv("QUIET_HOURS_END", "7"))  # hour to resume posting

# different prompts to keep things interesting  
PROMPT_TEMPLATES = {
    "anime": [
        "share a hot take about a popular anime",
        "recommend an underrated anime that deserves more love",
        "complain about a common anime trope in a funny way",
        "describe what its like waiting for your favorite anime to get a new season",
        "make a joke about anime fans",
    ],
    "gaming": [
        "share a gaming opinion thatll start arguments",
        "describe a frustrating gaming moment everyone can relate to",
        "recommend an indie game people are sleeping on",
        "make fun of a gaming trend",
        "share a nostalgic gaming memory",
    ],
    "tech": [
        "complain about a tech problem everyone deals with",
        "share a hot take about a popular tech product",
        "joke about programmers or tech workers",
        "share a tech tip in a casual way",
        "make fun of tech hype",
    ],
}

PERSONALITY_PROMPTS = {
    "chill": "Write in a relaxed, casual tone. Be friendly but not too excited. Use lowercase mostly.",
    "hyped": "Write with energy and enthusiasm! Use caps sometimes, emojis are okay. Be fun!",
    "shitpost": "Write in an ironic, slightly unhinged way. Be absurd but still coherent. very lowercase, questionable grammar is a vibe",
}

HASHTAGS = {
    "anime": ["#anime", "#weeb", "#otaku", "#animememes"],
    "gaming": ["#gaming", "#gamer", "#videogames", "#indiegames"],
    "tech": ["#tech", "#programming", "#coding", "#developer"],
}

# Logging configuration
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("miyukibot")

# Twitter client placeholders
twitter_client = None
twitter_api = None

# --- Utilities ---

def save_json(path: Path, data: Any) -> None:
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Could not write %s: %s", path, e)


def load_json(path: Path, default: Any = None) -> Any:
    default = [] if default is None else default
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load %s: %s", path, e)
        return default


def ensure_memory_files() -> None:
    for v in MEMORY_FILES.values():
        if not v.exists():
            save_json(v, [])


def current_month_key() -> str:
    t = datetime.date.today()
    return f"{t.year}-{t.month:02d}"


def can_post() -> bool:
    data = load_json(COUNTER_FILE, {})
    key = current_month_key()
    count = data.get(key, 0)
    if count >= MAX_POSTS_PER_MONTH:
        logger.warning("Monthly limit reached (%d/%d)", count, MAX_POSTS_PER_MONTH)
        return False
    return True


def increment_count() -> None:
    data = load_json(COUNTER_FILE, {})
    key = current_month_key()
    data[key] = data.get(key, 0) + 1
    save_json(COUNTER_FILE, data)

# --- Image utilities ---

def pick_random_image_path() -> Optional[Path]:
    if not IMAGE_FOLDER.exists() or not IMAGE_FOLDER.is_dir():
        return None
    files = [p for p in IMAGE_FOLDER.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'} and p.is_file()]
    if not files:
        return None
    return random.choice(files)


def get_image_b64(path: Path) -> Optional[str]:
    try:
        if not path.exists():
            logger.debug("Image not found: %s", path)
            return None
        if path.stat().st_size > MAX_IMAGE_SIZE:
            logger.debug("Image too large: %s", path)
            return None
        with path.open("rb") as f:
            return f.read().encode('base64').decode('ascii') if False else __import__('base64').b64encode(f.read()).decode('ascii')
    except Exception as e:
        logger.debug("Failed to read image %s: %s", path, e)
        return None

# --- Text preprocessing & similarity (simple token set) ---

def preprocess_text_for_similarity(text: str) -> set:
    if not isinstance(text, str):
        return set()
    text = __import__('re').sub(r'http\S+|www\S+|https\S+', '', text, flags=__import__('re').IGNORECASE)
    text = __import__('re').sub(r'@\w+|#\w+', '', text)
    text = __import__('re').sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    return set(w for w in words if len(w) > 1)


def is_similar_to_history(new_text: str, history: List[Dict[str, Any]], threshold: float) -> bool:
    new_words = preprocess_text_for_similarity(new_text)
    if not new_words:
        return False
    for entry in history:
        hist_words = preprocess_text_for_similarity(entry.get("text", ""))
        if not hist_words:
            continue
        union = new_words | hist_words
        sim = len(new_words & hist_words) / len(union) if union else 0.0
        if sim >= threshold:
            return True
    return False


def clean_old_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=MEMORY_DURATION_DAYS)
    out = []
    for e in history:
        try:
            ts = datetime.datetime.fromisoformat(e.get("timestamp"))
            if ts >= cutoff:
                out.append(e)
        except Exception:
            continue
    return out


def load_history(mem_file: Path) -> List[Dict[str, Any]]:
    history = load_json(mem_file, [])
    return clean_old_history(history)

# --- Health monitoring ---

def health_check() -> Dict[str, bool]:
    status = {"ollama": False, "twitter": False, "newsapi": False, "disk_space": False}
    # Ollama
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)
        status["ollama"] = r.status_code == 200
    except Exception:
        status["ollama"] = False
    # Twitter
    status["twitter"] = TWEETY_AVAILABLE and twitter_client is not None
    # NewsAPI
    status["newsapi"] = bool(NEWSAPI_KEY)
    # Disk space
    try:
        free_bytes = os.statvfs(str(IMAGE_FOLDER)).f_bavail * os.statvfs(str(IMAGE_FOLDER)).f_frsize
        status["disk_space"] = free_bytes > (1024**3)
    except Exception:
        status["disk_space"] = True
    return status

# --- Ollama generation ---

def ollama_request_with_retry(endpoint: str, payload: Dict[str, Any], max_retries: int = 3) -> Optional[Dict[str, Any]]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Ollama request attempt %d failed: %s", attempt + 1, e)
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) + random.random())
    return None


def build_system_prompt(category: str = "anime") -> str:
    personality_hint = PERSONALITY_PROMPTS.get(PERSONALITY_MODE, PERSONALITY_PROMPTS["chill"])
    return (
        f"You are a twitter account that posts about {category}. "
        f"{personality_hint} "
        "Keep it under 250 characters. Dont use quotes around the tweet. Just output the tweet text, nothing else."
    )


def generate_with_ollama(user_prompt: str, image_path: Optional[Path] = None) -> Optional[str]:
    messages = [{"role": "system", "content": build_system_prompt()}, {"role": "user", "content": user_prompt}]
    b64 = get_image_b64(image_path) if image_path else None
    if b64 and isinstance(messages[1], dict):
        messages[1]["images"] = [b64]
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.7, "num_predict": 100}}
    res = ollama_request_with_retry("api/chat", payload)
    if res:
        return res.get("message", {}).get("content", "").strip()
    return None


def generate_with_ollama_v2(user_prompt: str, category: str, image_path: Optional[Path] = None) -> Optional[str]:
    """newer version that uses category-aware prompts"""
    messages = [
        {"role": "system", "content": build_system_prompt(category)}, 
        {"role": "user", "content": user_prompt}
    ]
    b64 = get_image_b64(image_path) if image_path else None
    if b64 and isinstance(messages[1], dict):
        messages[1]["images"] = [b64]
    
    # slightly higher temp for more creative outputs
    temp = 0.8 if PERSONALITY_MODE == "shitpost" else 0.7
    payload = {
        "model": OLLAMA_MODEL, 
        "messages": messages, 
        "stream": False, 
        "options": {"temperature": temp, "num_predict": 120}
    }
    res = ollama_request_with_retry("api/chat", payload)
    if res:
        return res.get("message", {}).get("content", "").strip()
    return None

# --- Twitter integration ---

def init_twitter_client() -> None:
    global twitter_client, twitter_api
    if not TWEETY_AVAILABLE:
        logger.info("Tweepy not installed; running in simulation mode.")
        return
    if not (TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET):
        logger.info("Twitter credentials not provided; running in simulation mode.")
        return
    try:
        twitter_client = tweepy.Client(
            bearer_token=None,  # bearer not required for OAuth1.0a post-only flow
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET,
            wait_on_rate_limit=True,
        )
        auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        twitter_api = tweepy.API(auth)
        logger.info("Twitter client initialized")
    except Exception as e:
        logger.exception("Failed to initialize Twitter client: %s", e)
        twitter_client = None
        twitter_api = None


def post_tweet(text: str, image_path: Optional[Path] = None) -> Optional[str]:
    """Post the tweet. Returns tweet id if posted, None in simulation or error."""
    if not TWEETY_AVAILABLE or twitter_client is None or twitter_api is None:
        logger.info("[SIMULATION] Tweet: %s", text)
        if image_path:
            logger.info("[SIMULATION] Image: %s", image_path)
        return None
    try:
        media_id = None
        if image_path:
            # Upload image (ensure file size limit)
            res = twitter_api.media_upload(str(image_path))
            media_id = res.media_id
        logger.info("Posting tweet: %s", text[:80])
        response = twitter_client.create_tweet(text=text, media_ids=[media_id] if media_id else None)
        tweet_id = None
        if response and getattr(response, 'data', None):
            tweet_id = response.data.get('id') if isinstance(response.data, dict) else None
        logger.info("Tweet posted: %s", tweet_id)
        return tweet_id
    except Exception as e:
        logger.exception("Failed to post tweet: %s", e)
        return None

# --- Content generators ---

def is_quiet_hours() -> bool:
    """check if we're in quiet hours (dont post late at night)"""
    hour = datetime.datetime.now().hour
    if QUIET_HOURS_START < QUIET_HOURS_END:
        return QUIET_HOURS_START <= hour < QUIET_HOURS_END
    else:  # wraps around midnight
        return hour >= QUIET_HOURS_START or hour < QUIET_HOURS_END


def pick_random_category() -> str:
    """pick a random content category"""
    return random.choice(list(PROMPT_TEMPLATES.keys()))


def pick_random_prompt(category: str) -> str:
    """get a random prompt for the category"""
    prompts = PROMPT_TEMPLATES.get(category, PROMPT_TEMPLATES["anime"])
    return random.choice(prompts)


def maybe_add_hashtags(text: str, category: str) -> str:
    """sometimes add a hashtag or two"""
    if not USE_HASHTAGS:
        return text
    if random.random() > 0.6:  # 40% chance to add hashtags
        return text
    tags = HASHTAGS.get(category, [])
    if tags:
        tag = random.choice(tags)
        if len(text) + len(tag) < 275:  # leave room
            text = f"{text} {tag}"
    return text


def try_post_generated() -> bool:
    # check quiet hours
    if is_quiet_hours():
        logger.info("in quiet hours, skipping post")
        return False
    
    ensure_memory_files()
    mem_file = MEMORY_FILES.get("questions")
    history = load_history(mem_file)
    
    # pick random category and prompt
    category = pick_random_category()
    prompt = pick_random_prompt(category)
    
    image_path = pick_random_image_path()
    text = generate_with_ollama_v2(prompt, category, image_path)
    if not text:
        logger.debug("No text generated")
        return False
    
    # clean up the text a bit
    text = text.strip('"').strip("'").strip()
    
    if is_similar_to_history(text, history, SIMILARITY_THRESHOLD):
        logger.debug("Generated text too similar to history; skipping")
        return False
    
    # maybe add hashtags
    text = maybe_add_hashtags(text, category)
    
    tweet_id = post_tweet(text, image_path)
    
    # Save memory
    entry = {
        "text": text, 
        "timestamp": datetime.datetime.now().isoformat(), 
        "category": category,
        "personality": PERSONALITY_MODE
    }
    history.append(entry)
    save_json(mem_file, history)
    
    if tweet_id:
        track_tweet_performance(str(tweet_id), text, category)
    increment_count()
    return True

# --- Analytics ---

def track_tweet_performance(tweet_id: str, text: str, category: str) -> None:
    data = load_json(ANALYTICS_FILE, {"tweets": []})
    data.setdefault("tweets", []).append({"id": tweet_id, "text": text, "category": category, "timestamp": datetime.datetime.now().isoformat()})
    data["tweets"] = data["tweets"][-200:]
    save_json(ANALYTICS_FILE, data)

# --- Main loop ---

def main_run():
    logger.info("=" * 50)
    logger.info("miyuki-bot v%s starting up!", VERSION)
    logger.info("personality: %s | interval: %ds | hashtags: %s", 
                PERSONALITY_MODE, POST_INTERVAL_SECONDS, USE_HASHTAGS)
    if QUIET_HOURS_START != QUIET_HOURS_END:
        logger.info("quiet hours: %d:00 - %d:00", QUIET_HOURS_START, QUIET_HOURS_END)
    logger.info("=" * 50)
    
    init_twitter_client()
    health = health_check()
    logger.info("health check: ollama=%s twitter=%s", 
                "ok" if health["ollama"] else "nope", 
                "ok" if health["twitter"] else "simulation mode")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            logger.info("--- cycle %d ---", cycle)
            
            if can_post():
                posted = try_post_generated()
                if posted:
                    logger.info("posted something! nice")
                else:
                    logger.info("nothing posted this cycle (maybe quiet hours or similar content)")
            else:
                logger.info("at monthly limit, chilling")
            
            logger.info("sleeping for %d seconds...", POST_INTERVAL_SECONDS)
            time.sleep(POST_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logger.info("shutting down, bye!")
            break
        except Exception as e:
            logger.exception("oop something broke: %s", e)
            time.sleep(60)


if __name__ == '__main__':
    main_run()
