# Blynex SEO & LLM Audit Utility

A serverless Python tool deployed on Modal infrastructure that runs automated Core Web Vitals diagnostics, schema markup checks, and `llms.txt` crawlability audits.

Developed and maintained by **[Blynex Solution](https://blynexsolution.com)** — High-Performance Web Engineering & Modern Search Strategy.

## ⚡ Overview
This serverless utility gives web developers and SEO engineers quick performance diagnostics and AI search agent validation via Modal cloud endpoints.

## 🚀 Key Features
* **Core Web Vitals Verification:** Analyzes LCP rendering paths and structural layout shifts.
* **LLM & AI Agent Audit:** Validates site readability against machine protocols (`llms.txt` and schema data).
* **Modal Serverless Deployment:** Runs on-demand with zero server overhead.

## 🛠️ Local Usage & Deployment
To run or deploy this utility using Modal CLI:

```bash
pip install modal
modal setup
modal deploy app.py
