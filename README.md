# 🧠 LLaMA-Powered Autonomous News Poster

A self-contained Python bot designed to autonomously fetch trending news, generate original summaries, and post them to Twitter/X — all with an elegant, personality-infused tone powered by **Meta LLaMA 3.1 8B Instruct (GGUF)**.

> ⚠️ Source code is **not public** due to proprietary design, security considerations, and future deployment plans.

---

## ✨ Key Features

- 🦙 **Meta LLaMA 3.1 8B Instruct (GGUF)** for high-quality text generation
- 📰 Integrates with **NewsAPI** to pull real-time headlines
- 💬 Generates personalized summaries with stylistic personality
- 🧠 Local memory system avoids repeated posts (Jaccard similarity)
- 🔍 Built-in content moderation and safety filtering
- ⚡ CUDA-enabled GPU inference via `llama-cpp-python`
- 📤 Auto-posts to Twitter/X via **v2 API + Tweepy**
- 🧩 Modular structure — easily scheduler-integrated

---

## 🛠️ Tech Stack

| Component          | Description                            |
|--------------------|----------------------------------------|
| Python 3.11        | Core language                          |
| llama-cpp-python   | GGUF LLaMA 3.1 integration (cuBLAS)    |
| Tweepy (v2)        | X/Twitter posting                      |
| NewsAPI.org        | News content sourcing                  |
| JSON Storage       | Local memory and counters              |
| CUDA               | GPU offloading for inference           |

---

## 📸 Sample Output

> *“Oh my, this update brings such thoughtful innovation to the table. Always fascinating to watch the digital world evolve. ✨ What’s your take on it? #Tech #News”*

---

## 📁 Source Code

The implementation includes:
- LLM initialization with GPU offloading
- News fetching and filtering
- Tweet generation prompt logic
- Duplicate detection via similarity checks
- Moderation and auto-posting logic

🛡️ **Note:** The source code is private to maintain security (API keys), protect LLM prompt logic, and allow for future commercialization.

---

## 🚀 Deployment Ready

- Designed for use with task schedulers (e.g., cron, systemd, GUI wrappers)
- Lightweight, single-script execution
- Logs, fallbacks, and fail-safes included

---

## 📩 Contact

Feel free to reach out for:
- Collaborations
- Private demo or walkthrough
- Technical discussions

**Vishnu Veenadharan**  
📧 Email: _vichu852002@gmail.com_  
🌐 GitHub: [www.github.com/Vishnu852002]

---

## 📄 License

All rights reserved.

This project is intended for demonstration purposes only.
No part of the source code, design, or logic may be used, copied, modified, or distributed without explicit written permission from the author.

© 2025 Vishnu Veenadharan
