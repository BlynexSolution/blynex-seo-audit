# Blynex SEO & LLM Audit Utility

A high-performance, serverless Python application deployed on Modal cloud infrastructure. It performs automated AI crawler protocol diagnostics (`llms.txt`, `agents.json`, `robots.txt`), Schema.org JSON-LD validation, and on-page semantic SEO audits.

Developed and maintained by **[Blynex Solution](https://blynexsolution.com)** — High-Performance Web Engineering, Digital Trust Architectures & Modern SEO.

---

## 🌐 Instant Live Web Access (No Setup Required)

You do not need to install anything to run an audit. You can access the hosted, live tool directly in your browser:

👉 **[Launch Blynex AI Readiness Tool](https://blynexsolution--blynex-ai-readiness-checker-fastapi-app.modal.run)**

> **How to use:**
> 1. Open the live link above.
> 2. Enter any website URL (e.g., `(https://yourwebsite.com)`) and your business email.
> 3. Click **Run Diagnostic** to generate your AI Indexing score, keyword insights, and instant code templates.
> 
> 

---

## 🚀 Key Features

* **🤖 AI Agent Protocol Verification:** Scans for machine-readable `/llms.txt` and `/agents.json` files.
* **🕷️ AI Crawler Permission Audit:** Checks if your `robots.txt` rules permit OpenAI (`GPTBot`), Perplexity (`PerplexityBot`), and Anthropic (`ClaudeBot`).
* **📐 Schema.org JSON-LD Validation:** Verifies structured entity data for search engines and AI language models.
* **🔍 On-Page Semantic SEO Inspection:** Analyzes Meta Titles, Meta Descriptions, and `<h1>`/`<h2>` heading counts for targeted keywords.
* **⚡ Dynamic Code Fixes:** Automatically generates ready-to-copy, custom code snippets for any missing protocol files.

---

## 🛠️ Step-by-Step Local Installation & Deployment Guide

Follow these steps if you want to run, modify, or deploy this utility on your own Modal cloud workspace.

### Prerequisites

Make sure you have **Python 3.10+** installed on your computer.

---

### Step 1: Download or Save `app.py`

Download this repository or copy `app.py` into a folder on your computer (e.g., `C:\Users\YourName\Downloads`).

---

### Step 2: Install Required Libraries

Open your Command Prompt (CMD), PowerShell, or Terminal and run this command:

```bash
python -m pip install modal fastapi beautifulsoup4 requests python-multipart

```

---

### Step 3: Authenticate with Modal

Connect your local machine to your free account on [Modal.com](https://modal.com):

```bash
python -m modal setup

```

> *This will open a browser tab. Click **Authorize** to log into your workspace.*

---

### Step 4: Deploy Live to Modal Cloud

Deploy your serverless app to the cloud:

```bash
python -m modal deploy app.py

```

🎉 **That's it!** Modal will immediately output your live HTTPS URL directly in the terminal. You can close your terminal and turn off your PC—your app will stay online 24/7 on Modal's cloud servers.

---

## 📬 Support & Engineering Services

Need help implementing custom AI discovery protocols, Schema architectures, or high-converting web infrastructure?

* **Official Website:** [blynexsolution.com](https://blynexsolution.com)
* **Direct Email:** [hello@blynexsolution.com](mailto:hello@blynexsolution.com)
* **Talk to an Engineer:** [Schedule an Audit Call](https://blynexsolution.com/contact/)
