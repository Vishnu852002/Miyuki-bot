"""MiyukiBot v1.0
Professional, privacy-safe, and GitHub-ready Twitter/Content bot skeleton.

Features:
- Ollama-based generation (local Ollama server)
- Optional Twitter posting via Tweepy (reads credentials from environment variables)
- Simulation mode if credentials are missing or when disabled
- Configurable via environment variables
- Health checks, safe defaults, and clear logging
- No personal data, hard-coded paths, or user-identifying comments

Usage:
1. Create a virtualenv and install requirements:
   pip install -r requirements.txt
   (requirements.txt should include: requests, tweepy)
2. Set environment variables (example):
   export OLLAMA_BASE_URL="http://localhost:11434"
   export OLLAMA_MODEL="gemma3:4B"
   export TWITTER_API_KEY="..."
   export TWITTER_API_SECRET="..."
   export TWITTER_ACCESS_TOKEN="..."
   export TWITTER_ACCESS_SECRET="..."
   export NEWSAPI_KEY="..."  # optional
3. Run:
   python newsbot_clean.py

The script is intentionally modular and documented for easy contribution on GitHub.
"""

from __future__ import annotations
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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4B")
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


def build_system_prompt() -> str:
    return (
        "You are an assistant that outputs a single short social-media-ready post about anime, gaming, or tech. "
        "Produce a concise, non-offensive post suitable for public social platforms. Output only the text of the post."
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

def try_post_generated() -> bool:
    ensure_memory_files()
    mem_file = MEMORY_FILES.get("questions")
    history = load_history(mem_file)
    prompt = "Write a concise, neutral, and interesting observation about anime/gaming/tech suitable for a general audience."
    image_path = pick_random_image_path()
    text = generate_with_ollama(prompt, image_path)
    if not text:
        logger.debug("No text generated")
        return False
    if is_similar_to_history(text, history, SIMILARITY_THRESHOLD):
        logger.debug("Generated text too similar to history; skipping")
        return False
    tweet_id = post_tweet(text, image_path)
    # Save memory
    entry = {"text": text, "timestamp": datetime.datetime.now().isoformat(), "category": "generated"}
    history.append(entry)
    save_json(mem_file, history)
    if tweet_id:
        # track analytics basic
        track_tweet_performance(str(tweet_id), text, "generated")
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
    logger.info("MiyukiBot starting. Interval %d seconds", POST_INTERVAL_SECONDS)
    init_twitter_client()
    logger.info("Initial health: %s", health_check())
    cycle = 0
    while True:
        try:
            cycle += 1
            logger.info("Cycle #%d", cycle)
            if can_post():
                posted = try_post_generated()
                if posted:
                    logger.info("Posted content in cycle %d", cycle)
                else:
                    logger.info("No content posted in cycle %d", cycle)
            else:
                logger.info("Skipping post due to monthly limit")
            logger.info("Sleeping %d seconds", POST_INTERVAL_SECONDS)
            time.sleep(POST_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("Shutting down")
            break
        except Exception as e:
            logger.exception("Unexpected error in main loop: %s", e)
            time.sleep(60)


if __name__ == '__main__':
    main_run()
