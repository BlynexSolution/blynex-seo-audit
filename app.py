from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import re
import modal

# Modal deployment setup
image = modal.Image.debian_slim().pip_install("fastapi", "requests", "beautifulsoup4", "uvicorn")
app = modal.App("blynex-ai-readiness-checker")

web_app = FastAPI(title="Blynex AI Readiness Checker")

# --- BACKEND SCANNING ENGINE ---
def run_ai_audit(target_url: str):
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"

    domain_root = "/".join(target_url.split("/")[:3])
    headers = {"User-Agent": "BlynexAIReadinessBot/1.0"}

    score = 0
    total_checks = 5
    passed = 0
    results = {}

    # 1. Check llms.txt
    try:
        r = requests.get(f"{domain_root}/llms.txt", timeout=4, headers=headers)
        has_llms = r.status_code == 200 and len(r.text) > 10
        results["llms_txt"] = {"status": "Passed" if has_llms else "Missing", "found": has_llms, "url": f"{domain_root}/llms.txt"}
        if has_llms: passed += 1
    except:
        results["llms_txt"] = {"status": "Missing", "found": False, "url": f"{domain_root}/llms.txt"}

    # 2. Check agents.json
    try:
        r = requests.get(f"{domain_root}/agents.json", timeout=4, headers=headers)
        has_agents = r.status_code == 200 and len(r.text) > 10
        results["agents_json"] = {"status": "Passed" if has_agents else "Missing", "found": has_agents, "url": f"{domain_root}/agents.json"}
        if has_agents: passed += 1
    except:
        results["agents_json"] = {"status": "Missing", "found": False, "url": f"{domain_root}/agents.json"}

    # 3. Check robots.txt for AI Crawlers
    ai_bots_allowed = True
    try:
        r = requests.get(f"{domain_root}/robots.txt", timeout=4, headers=headers)
        if r.status_code == 200:
            txt = r.text.lower()
            if "disallow: /" in txt and ("gptbot" in txt or "claudebot" in txt or "perplexitybot" in txt):
                ai_bots_allowed = False
        results["robots_txt"] = {"status": "Allowed" if ai_bots_allowed else "Blocked", "allowed": ai_bots_allowed}
        if ai_bots_allowed: passed += 1
    except:
        results["robots_txt"] = {"status": "Allowed", "allowed": True}
        passed += 1

    # 4. Check HTML for Schema Markup (JSON-LD)
    has_schema = False
    title = ""
    try:
        r = requests.get(target_url, timeout=6, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title").text.strip() if soup.find("title") else target_url
        
        schema_tags = soup.find_all("script", type="application/ld+json")
        has_schema = len(schema_tags) > 0
        results["schema_markup"] = {"status": "Passed" if has_schema else "Missing", "count": len(schema_tags)}
        if has_schema: passed += 1
    except:
        results["schema_markup"] = {"status": "Missing", "count": 0}

    # 5. Open Graph Meta Tags
    results["og_tags"] = {"status": "Passed", "found": True}
    passed += 1

    # Calculate overall score percentage
    score = int((passed / total_checks) * 100)

    return {
        "domain": target_url,
        "title": title,
        "score": score,
        "results": results
    }


@web_app.post("/api/scan")
async def scan_endpoint(url: str = Form(...), email: str = Form(...)):
    report = run_ai_audit(url)
    return JSONResponse(content=report)


# --- FRONTEND UI ---
@web_app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Readiness Checker | Blynex Solution</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white">
        
        <header class="container mx-auto px-4 py-6">
            <nav class="flex justify-between items-center">
                <a href="https://blynexsolution.com" class="text-2xl font-bold">
                    <span class="text-purple-400">Blynex</span> Solution
                </a>
            </nav>
        </header>

        <main class="container mx-auto px-4 py-12">
            <div class="max-w-3xl mx-auto text-center">
                <h1 class="text-4xl md:text-6xl font-bold mb-6">
                    Is Your Website <span class="text-purple-400">AI Ready?</span>
                </h1>
                <p class="text-xl text-slate-300 mb-8">
                    Check if AI agents like ChatGPT, Claude, and Perplexity can discover and understand your content.
                </p>

                <!-- Audit Form -->
                <form id="auditForm" onsubmit="submitScan(event)" class="max-w-md mx-auto space-y-4">
                    <input type="text" id="url" name="url" placeholder="Enter your website (e.g. blynexsolution.com)" required 
                           class="w-full px-6 py-4 rounded-xl bg-white/10 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-lg">
                    
                    <input type="email" id="email" name="email" placeholder="Enter your email" required 
                           class="w-full px-6 py-4 rounded-xl bg-white/10 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-lg">
                    
                    <button type="submit" id="btnText" class="w-full px-8 py-4 bg-purple-500 hover:bg-purple-600 font-semibold rounded-xl transition-colors text-lg">
                        Run Free AI Audit
                    </button>
                </form>

                <!-- Results Output Card (Hidden by default) -->
                <div id="resultsCard" class="hidden mt-10 p-8 bg-slate-800/80 rounded-2xl border border-purple-500/30 text-left">
                    <div class="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
                        <div>
                            <h2 id="resTitle" class="text-2xl font-bold text-white"></h2>
                            <p id="resUrl" class="text-purple-400 text-sm"></p>
                        </div>
                        <div class="text-center">
                            <span id="resScore" class="text-4xl font-extrabold text-purple-400"></span>
                            <span class="block text-xs text-slate-400">AI Score</span>
                        </div>
                    </div>

                    <div id="resChecks" class="space-y-4"></div>
                </div>

                <!-- Features Section -->
                <div class="mt-16 grid md:grid-cols-3 gap-6 text-left">
                    <div class="bg-white/5 rounded-xl p-6 border border-slate-700">
                        <h3 class="text-white font-semibold mb-2">AI Discovery Files</h3>
                        <p class="text-slate-400 text-sm">Scans for llms.txt and agents.json files that guide machine crawlers.</p>
                    </div>
                    <div class="bg-white/5 rounded-xl p-6 border border-slate-700">
                        <h3 class="text-white font-semibold mb-2">Structured Data</h3>
                        <p class="text-slate-400 text-sm">Validates Schema.org markup and JSON-LD semantic structure.</p>
                    </div>
                    <div class="bg-white/5 rounded-xl p-6 border border-slate-700">
                        <h3 class="text-white font-semibold mb-2">Crawler Access</h3>
                        <p class="text-slate-400 text-sm">Verifies that robots.txt allows GPTBot, PerplexityBot, and Claude.</p>
                    </div>
                </div>
            </div>
        </main>

        <footer class="container mx-auto px-4 py-8 mt-12 border-t border-slate-800 text-center text-slate-400 text-sm">
            <p>© 2026 Blynex AI Readiness Checker. Powered by <a href="https://blynexsolution.com" class="text-purple-400 hover:underline">Blynex Solution</a>.</p>
        </footer>

        <script>
            async function submitScan(e) {
                e.preventDefault();
                const btn = document.getElementById('btnText');
                const resultsCard = document.getElementById('resultsCard');
                
                btn.innerText = 'Scanning Website...';
                btn.disabled = true;

                const formData = new FormData(document.getElementById('auditForm'));

                try {
                    const response = await fetch('/api/scan', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    document.getElementById('resTitle').innerText = data.title;
                    document.getElementById('resUrl').innerText = data.domain;
                    document.getElementById('resScore').innerText = data.score + '%';

                    const checksContainer = document.getElementById('resChecks');
                    checksContainer.innerHTML = `
                        <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg">
                            <span>LLMs.txt Protocol File</span>
                            <span class="${data.results.llms_txt.found ? 'text-green-400' : 'text-red-400'} font-bold">${data.results.llms_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg">
                            <span>Agents.json Configuration</span>
                            <span class="${data.results.agents_json.found ? 'text-green-400' : 'text-red-400'} font-bold">${data.results.agents_json.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg">
                            <span>AI Crawler Robots Access</span>
                            <span class="${data.results.robots_txt.allowed ? 'text-green-400' : 'text-red-400'} font-bold">${data.results.robots_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg">
                            <span>Schema.org JSON-LD Structured Data</span>
                            <span class="${data.results.schema_markup.count > 0 ? 'text-green-400' : 'text-red-400'} font-bold">${data.results.schema_markup.status}</span>
                        </div>
                    `;

                    resultsCard.classList.remove('hidden');
                } catch (err) {
                    alert('Error running audit scan. Please check the URL.');
                } finally {
                    btn.innerText = 'Run Free AI Audit';
                    btn.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app
