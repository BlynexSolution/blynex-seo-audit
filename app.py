from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import modal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

# Modal deployment container setup
image = modal.Image.debian_slim().pip_install(
    "fastapi", "requests", "beautifulsoup4", "uvicorn", "python-multipart"
)
app = modal.App("blynex-ai-readiness-checker")

web_app = FastAPI(title="Blynex Solution - AI Readiness Checker")

# --- LEAD NOTIFICATION SYSTEM ---
NOTIFICATION_EMAIL = "hello@blynexsolution.com"

def send_lead_notification(scanned_url: str, user_email: str, ai_score: int):
    """Sends background email alert when a new lead scans their site."""
    try:
        # Standard SMTP lead alert structure
        msg = MIMEMultipart()
        msg['Subject'] = f"🚀 New AI Audit Lead: {scanned_url} ({ai_score}% Score)"
        msg['From'] = "Blynex Audit Engine <noreply@blynexsolution.com>"
        msg['To'] = NOTIFICATION_EMAIL

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #0c0d18; color: #ffffff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #12142b; padding: 30px; border-radius: 12px; border: 1px solid #1a1aff;">
                    <h2 style="color: #3a3aff; margin-top: 0;">🔥 New AI Audit Lead Generated!</h2>
                    <p style="font-size: 16px;">A prospective client just ran an AI Readiness Audit on your tool:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <tr style="border-bottom: 1px solid #282b52;">
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">Scanned Website:</td>
                            <td style="padding: 10px; color: #ffffff;">{scanned_url}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #282b52;">
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">User Email:</td>
                            <td style="padding: 10px; color: #ffffff;"><a href="mailto:{user_email}" style="color: #3a3aff;">{user_email}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">AI Readiness Score:</td>
                            <td style="padding: 10px; font-weight: bold; color: #00d084;">{ai_score}%</td>
                        </tr>
                    </table>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="mailto:{user_email}?subject=Your%20Blynex%20AI%20Readiness%20Audit%20Results" 
                           style="background: linear-gradient(135deg, #111172 0%, #1a1aff 100%); color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                           Follow Up With Lead
                        </a>
                    </div>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        print(f"[LEAD CAPTURED] Website: {scanned_url} | Email: {user_email} | Score: {ai_score}%")
    except Exception as e:
        print(f"Lead notification log: {e}")


# --- AUDIT ENGINE ---
def run_ai_audit(target_url: str):
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"

    domain_root = "/".join(target_url.split("/")[:3])
    headers = {"User-Agent": "BlynexAIReadinessBot/1.0"}

    total_checks = 4
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

    # 4. Check HTML Schema Markup (JSON-LD)
    title = target_url
    try:
        r = requests.get(target_url, timeout=5, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title").text.strip() if soup.find("title") else target_url
        schema_tags = soup.find_all("script", type="application/ld+json")
        has_schema = len(schema_tags) > 0
        results["schema_markup"] = {"status": "Passed" if has_schema else "Missing", "count": len(schema_tags)}
        if has_schema: passed += 1
    except:
        results["schema_markup"] = {"status": "Missing", "count": 0}

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
    
    # Send email notification in non-blocking thread
    threading.Thread(
        target=send_lead_notification, 
        args=(report["domain"], email, report["score"])
    ).start()

    return JSONResponse(content=report)


# --- FRONTEND (BLYNEX BRANDED UI) ---
@web_app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Readiness Checker | Blynex Solution</title>
        <link rel="icon" href="https://blynexsolution.com/wp-content/uploads/2026/04/Site-Favicon-150x150.png" sizes="32x32">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Red+Hat+Text:wght@400;600;700&display=swap" rel="stylesheet">
        
        <style>
            body {
                font-family: 'Red Hat Text', 'Inter', sans-serif;
                background-color: #090a16;
                color: #ffffff;
            }
            .blynex-btn {
                background: linear-gradient(135deg, rgba(17, 17, 114, 0.9) 0%, rgba(26, 26, 255, 0.8) 100%) !important;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.35), 0 4px 20px rgba(26, 26, 255, 0.3) !important;
                transition: all 0.3s ease !important;
            }
            .blynex-btn:hover {
                background: linear-gradient(135deg, rgba(26, 26, 255, 0.95) 0%, rgba(58, 58, 255, 0.9) 100%) !important;
                transform: translateY(-2px);
                box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.5), 0 8px 28px rgba(26, 26, 255, 0.5) !important;
            }
            .blynex-card {
                background: rgba(18, 20, 43, 0.6);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .blynex-glow {
                text-shadow: 0 0 20px rgba(26, 26, 255, 0.6);
            }
        </style>
    </head>
    <body class="min-h-screen flex flex-col justify-between">
        
        <!-- Header -->
        <header class="container mx-auto px-6 py-6 border-b border-white/10">
            <nav class="flex justify-between items-center">
                <a href="https://blynexsolution.com/">
                    <img src="https://blynexsolution.com/wp-content/uploads/2026/04/Site-Logo-01.svg" alt="Blynex Solution Logo" class="h-10">
                </a>
                <a href="https://blynexsolution.com/contact/" class="blynex-btn hidden md:inline-block px-6 py-2.5 rounded-md font-semibold text-xs tracking-widest uppercase">
                    Get In Touch
                </a>
            </nav>
        </header>

        <!-- Hero Content -->
        <main class="container mx-auto px-4 py-12 md:py-20 my-auto">
            <div class="max-w-3xl mx-auto text-center">
                
                <p class="text-xs font-bold tracking-widest uppercase text-indigo-400 mb-3">AI Discovery & Engineering Diagnostic</p>
                
                <h1 class="text-4xl md:text-6xl font-bold tracking-tight mb-6">
                    Is Your Website <span class="text-indigo-400 blynex-glow">AI Ready?</span>
                </h1>
                
                <p class="text-lg md:text-xl text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
                    Verify if modern AI engines like ChatGPT, Claude, and Perplexity can seamlessly index, parse, and cite your brand.
                </p>

                <!-- Audit Form -->
                <form id="auditForm" onsubmit="submitScan(event)" class="max-w-md mx-auto space-y-4">
                    <input type="text" id="url" name="url" placeholder="https://yourwebsite.com" required 
                           class="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 text-base">
                    
                    <input type="email" id="email" name="email" placeholder="Enter your business email" required 
                           class="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 text-base">
                    
                    <button type="submit" id="btnText" class="w-full blynex-btn py-4 rounded-xl font-bold uppercase tracking-wider text-sm">
                        RUN FREE AI AUDIT
                    </button>
                </form>

                <!-- Results Output Card -->
                <div id="resultsCard" class="hidden mt-12 p-8 blynex-card rounded-2xl text-left shadow-2xl">
                    <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                        <div>
                            <h2 id="resTitle" class="text-2xl font-bold text-white"></h2>
                            <p id="resUrl" class="text-indigo-400 text-sm font-mono mt-1"></p>
                        </div>
                        <div class="text-center bg-indigo-950/60 border border-indigo-500/30 px-6 py-3 rounded-xl">
                            <span id="resScore" class="text-4xl font-extrabold text-indigo-400"></span>
                            <span class="block text-xs uppercase tracking-wider text-slate-400 mt-0.5">AI Readiness</span>
                        </div>
                    </div>

                    <div id="resChecks" class="space-y-3"></div>

                    <div class="mt-8 pt-6 border-t border-white/10 text-center">
                        <p class="text-sm text-slate-300 mb-4">Need help implementing <code class="text-indigo-300">llms.txt</code> or Schema structure for your site?</p>
                        <a href="https://blynexsolution.com/contact/" target="_blank" class="blynex-btn inline-block px-8 py-3 rounded-lg font-bold text-xs uppercase tracking-widest">
                            TALK TO A BLYNEX ENGINEER
                        </a>
                    </div>
                </div>

                <!-- Core Pillars Grid -->
                <div class="mt-20 grid md:grid-cols-3 gap-6 text-left">
                    <div class="blynex-card rounded-xl p-6">
                        <div class="w-10 h-10 rounded-lg bg-indigo-600/20 flex items-center justify-center mb-4 text-indigo-400 font-bold">01</div>
                        <h3 class="text-white font-bold mb-2">AI Discovery Files</h3>
                        <p class="text-slate-400 text-sm leading-relaxed">Scans for dedicated llms.txt and agents.json files that provide context to machine agents.</p>
                    </div>
                    <div class="blynex-card rounded-xl p-6">
                        <div class="w-10 h-10 rounded-lg bg-indigo-600/20 flex items-center justify-center mb-4 text-indigo-400 font-bold">02</div>
                        <h3 class="text-white font-bold mb-2">Schema Architecture</h3>
                        <p class="text-slate-400 text-sm leading-relaxed">Validates JSON-LD semantic structure so search algorithms understand entity relationships.</p>
                    </div>
                    <div class="blynex-card rounded-xl p-6">
                        <div class="w-10 h-10 rounded-lg bg-indigo-600/20 flex items-center justify-center mb-4 text-indigo-400 font-bold">03</div>
                        <h3 class="text-white font-bold mb-2">Crawler Permissions</h3>
                        <p class="text-slate-400 text-sm leading-relaxed">Verifies robots.txt protocols permit GPTBot, PerplexityBot, and Claude scrapers.</p>
                    </div>
                </div>

            </div>
        </main>

        <!-- Footer -->
        <footer class="border-t border-white/10 bg-[#060710] py-12">
            <div class="container mx-auto px-6 text-center">
                <a href="https://blynexsolution.com/" class="inline-block mb-4">
                    <img src="https://blynexsolution.com/wp-content/uploads/2026/04/Blynex-Footer-Logo.png" alt="Blynex Footer Logo" class="h-12 mx-auto">
                </a>
                <p class="text-slate-400 text-sm max-w-xl mx-auto mb-6 leading-relaxed">
                    Blynex Solution builds high-performance digital infrastructure, WordPress engineering, and SEO for service-based businesses globally.
                </p>
                <div class="flex justify-center space-x-6 text-sm text-slate-400">
                    <a href="https://blynexsolution.com/services/" class="hover:text-white transition-colors">Services</a>
                    <a href="https://blynexsolution.com/work/" class="hover:text-white transition-colors">Work</a>
                    <a href="https://blynexsolution.com/about/" class="hover:text-white transition-colors">About</a>
                    <a href="https://blynexsolution.com/contact/" class="hover:text-white transition-colors">Contact</a>
                </div>
                <p class="text-slate-500 text-xs mt-8">© 2026 Blynex Solution. All rights reserved.</p>
            </div>
        </footer>

        <script>
            async function submitScan(e) {
                e.preventDefault();
                const btn = document.getElementById('btnText');
                const resultsCard = document.getElementById('resultsCard');
                
                btn.innerText = 'SCANNING INFRASTRUCTURE...';
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
                        <div class="flex justify-between items-center p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-sm font-medium">LLMs.txt Protocol File</span>
                            <span class="${data.results.llms_txt.found ? 'text-emerald-400' : 'text-rose-400'} font-bold text-sm uppercase tracking-wide">${data.results.llms_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-sm font-medium">Agents.json Configuration</span>
                            <span class="${data.results.agents_json.found ? 'text-emerald-400' : 'text-rose-400'} font-bold text-sm uppercase tracking-wide">${data.results.agents_json.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-sm font-medium">AI Crawler Robots Access</span>
                            <span class="${data.results.robots_txt.allowed ? 'text-emerald-400' : 'text-rose-400'} font-bold text-sm uppercase tracking-wide">${data.results.robots_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-sm font-medium">Schema.org JSON-LD Structured Data</span>
                            <span class="${data.results.schema_markup.count > 0 ? 'text-emerald-400' : 'text-rose-400'} font-bold text-sm uppercase tracking-wide">${data.results.schema_markup.status}</span>
                        </div>
                    `;

                    resultsCard.classList.remove('hidden');
                } catch (err) {
                    alert('Error scanning domain. Please verify the URL.');
                } finally {
                    btn.innerText = 'RUN FREE AI AUDIT';
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
