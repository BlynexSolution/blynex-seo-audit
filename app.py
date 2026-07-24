from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import modal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import json
import re

# Modal deployment container setup
image = modal.Image.debian_slim().pip_install(
    "fastapi", "requests", "beautifulsoup4", "uvicorn", "python-multipart"
)
# Match original deployment name to overwrite existing live URL
app = modal.App("blynex-ai-readiness-checker")

web_app = FastAPI(title="Blynex Solution - AI & SEO Diagnostic Utility")

# --- LEAD NOTIFICATION SYSTEM ---
NOTIFICATION_EMAIL = "hello@blynexsolution.com"

def send_lead_notification(scanned_url: str, user_email: str, ai_score: int, title: str, keywords_found: list):
    """Sends background email alert when a new lead runs an audit."""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"🔥 New AI Audit Lead: {scanned_url} ({ai_score}% Score)"
        msg['From'] = "Blynex Audit Engine <noreply@blynexsolution.com>"
        msg['To'] = NOTIFICATION_EMAIL

        kw_str = ", ".join(keywords_found[:3]) if keywords_found else "General Content"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #0c0d18; color: #ffffff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #12142b; padding: 30px; border-radius: 12px; border: 1px solid #1a1aff;">
                    <h2 style="color: #3a3aff; margin-top: 0;">🚀 New High-Intent Lead Captured!</h2>
                    <p style="font-size: 15px; color: #cccccc;">A user just scanned their site using the Blynex AI Readiness Tool:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <tr style="border-bottom: 1px solid #282b52;">
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">Scanned Website:</td>
                            <td style="padding: 10px; color: #ffffff;">{scanned_url}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #282b52;">
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">Lead Email:</td>
                            <td style="padding: 10px; color: #ffffff;"><a href="mailto:{user_email}" style="color: #3a3aff; font-weight: bold;">{user_email}</a></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #282b52;">
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">Detected Keywords:</td>
                            <td style="padding: 10px; color: #ffffff;">{kw_str}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; color: #8f93c9;">AI Readiness Score:</td>
                            <td style="padding: 10px; font-weight: bold; color: {'#00d084' if ai_score >= 75 else '#ff4d4d'};">{ai_score}%</td>
                        </tr>
                    </table>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="mailto:{user_email}?subject=Blynex%20AI%20%26%20SEO%20Audit%20Follow-up%20for%20{scanned_url}" 
                           style="background: linear-gradient(135deg, #111172 0%, #1a1aff 100%); color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                           Contact Lead Now
                        </a>
                    </div>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        print(f"[LEAD CAPTURED] Domain: {scanned_url} | Email: {user_email} | Score: {ai_score}%")
    except Exception as e:
        print(f"Lead notification log: {e}")


# --- ADVANCED SCRAPING ENGINE ---
def run_advanced_ai_audit(target_url: str):
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"

    domain_parts = target_url.split("/")
    domain_root = "/".join(domain_parts[:3])
    clean_domain = domain_parts[2].replace("www.", "")
    brand_name = clean_domain.split('.')[0].capitalize()
    headers = {"User-Agent": "BlynexAIReadinessBot/11.0 (Semantic SEO Utility)"}

    total_checks = 4
    passed = 0
    results = {}
    fixes = []

    # --- 1. DEEP ON-PAGE SEO SCRAPE ---
    title_text = "Missing Title"
    meta_desc_text = "Missing Meta Description"
    h1_count = 0
    h2_count = 0
    raw_keywords_found = []

    try:
        r_page = requests.get(target_url, timeout=7, headers=headers)
        soup = BeautifulSoup(r_page.text, "html.parser")
        
        # Meta Title
        title_tag = soup.find("title")
        if title_tag and title_tag.text.strip():
            title_text = title_tag.text.strip()

        # Meta Description
        meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_desc_tag and meta_desc_tag.get("content"):
            meta_desc_text = meta_desc_tag.get("content").strip()

        # Headings Count
        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)
        h2_tags = soup.find_all("h2")
        h2_count = len(h2_tags)

        # --- EXTRACT TARGETED KEYWORDS & HEADLINES ---
        headings = [h.text.strip() for h in soup.find_all(["h1", "h2", "h3"]) if len(h.text.strip()) > 5]
        ignore_list = ["menu", "navigation", "footer", "search", "about", "contact", "copyright", "subscribe", 
                       "home", "latest", "recent", "login", "categories", "read more"]
        
        for h in headings:
            if not any(bad in h.lower() for bad in ignore_list):
                if h not in raw_keywords_found:
                    raw_keywords_found.append(h)

        if not raw_keywords_found:
            raw_keywords_found = [title_text]

        # Schema JSON-LD Check
        schema_tags = soup.find_all("script", type="application/ld+json")
        has_schema = len(schema_tags) > 0
        results["schema_markup"] = {"status": "Passed" if has_schema else "Missing", "count": len(schema_tags)}
        if has_schema:
            passed += 1
        else:
            fixes.append({
                "title": "Add Schema.org JSON-LD Structured Data",
                "problem": "Search engines and AI crawlers lack deterministic structured data about your website entity or publisher status.",
                "solution": "Embed a semantic 'WebSite', 'Organization', or 'Blog' Schema JSON-LD script into your <head>.",
                "code": f'<script type="application/ld+json">\n{{\n  "@context": "https://schema.org",\n  "@type": "WebSite",\n  "name": "{brand_name}",\n  "url": "{domain_root}/",\n  "description": "{meta_desc_text[:100]}..."\n}}\n</script>'
            })

    except Exception as e:
        results["schema_markup"] = {"status": "Missing", "count": 0}
        raw_keywords_found = ["Unable to scrape page content"]

    # --- 2. LLMS.TXT FILE CHECK ---
    try:
        r_llms = requests.get(f"{domain_root}/llms.txt", timeout=4, headers=headers)
        has_llms = r_llms.status_code == 200 and len(r_llms.text) > 10
        results["llms_txt"] = {"status": "Passed" if has_llms else "Missing", "found": has_llms}
        if has_llms:
            passed += 1
        else:
            top_topic_list = "\n".join([f"- {t[:40]}" for t in raw_keywords_found[:3]])
            sample_llms = f"# {brand_name}\n\n> {meta_desc_text[:100] if meta_desc_text != 'Missing Meta Description' else 'Authoritative insights and digital resources.'}\n\n## Core Topics Covered\n{top_topic_list}\n\n## Official Links\n- Website: {domain_root}\n- Contact: {domain_root}/contact"
            fixes.append({
                "title": "Deploy an llms.txt Protocol File",
                "problem": "Your domain lacks an /llms.txt file. Modern AI engines (ChatGPT, Perplexity) need this to parse your site efficiently without wasting crawl budget.",
                "solution": "Create a file named 'llms.txt' in your root directory containing a markdown-formatted summary of your site.",
                "code": sample_llms
            })
    except:
        results["llms_txt"] = {"status": "Missing", "found": False}

    # --- 3. AGENTS.JSON FILE CHECK ---
    try:
        r_agents = requests.get(f"{domain_root}/agents.json", timeout=4, headers=headers)
        has_agents = r_agents.status_code == 200 and len(r_agents.text) > 10
        results["agents_json"] = {"status": "Passed" if has_agents else "Missing", "found": has_agents}
        if has_agents:
            passed += 1
        else:
            sample_agents = json.dumps({
                "name": brand_name,
                "url": domain_root,
                "agent_permissions": {"allow_chatgpt": True, "allow_claude": True, "allow_perplexity": True}
            }, indent=2)
            fixes.append({
                "title": "Configure agents.json Directives",
                "problem": "Missing /agents.json file. Autonomous AI agents use this semantic configuration to verify permissions and data endpoints.",
                "solution": "Place a valid 'agents.json' file in your root folder.",
                "code": sample_agents
            })
    except:
        results["agents_json"] = {"status": "Missing", "found": False}

    # --- 4. ROBOTS.TXT AI CRAWLER ACCESS CHECK ---
    ai_bots_allowed = True
    try:
        r_robots = requests.get(f"{domain_root}/robots.txt", timeout=4, headers=headers)
        if r_robots.status_code == 200:
            txt = r_robots.text.lower()
            if "disallow: /" in txt and ("gptbot" in txt or "claudebot" in txt or "perplexitybot" in txt):
                ai_bots_allowed = False
        results["robots_txt"] = {"status": "Allowed" if ai_bots_allowed else "Blocked", "allowed": ai_bots_allowed}
        if ai_bots_allowed:
            passed += 1
        else:
            fixes.append({
                "title": "Unblock AI Crawlers in robots.txt",
                "problem": "Your current robots.txt directives are actively blocking AI bots (GPTBot, PerplexityBot) from indexing your content.",
                "solution": "Add explicitly permitted User-Agent rules in your robots.txt file.",
                "code": "User-agent: GPTBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /"
            })
    except:
        results["robots_txt"] = {"status": "Allowed", "allowed": True}
        passed += 1

    score = int((passed / total_checks) * 100)

    return {
        "domain": target_url,
        "clean_domain": clean_domain,
        "brand_name": brand_name,
        "score": score,
        "results": results,
        "fixes": fixes,
        "seo_data": {
            "title": title_text,
            "meta_desc": meta_desc_text,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "targeted_keywords": raw_keywords_found[:5]
        }
    }


@web_app.post("/api/scan")
async def scan_endpoint(url: str = Form(...), email: str = Form(...)):
    report = run_advanced_ai_audit(url)
    
    # Non-blocking lead email notification
    threading.Thread(
        target=send_lead_notification, 
        args=(report["domain"], email, report["score"], report["seo_data"]["title"], report["seo_data"]["targeted_keywords"])
    ).start()

    return JSONResponse(content=report)


# --- FRONTEND UI ---
@web_app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
        <title>AI Readiness & Semantic SEO Diagnostic | Blynex Solution</title>
        <meta name="description" content="Audit your website for AI compatibility. Check if ChatGPT, Claude, and Perplexity can index your brand. Get free technical code fixes and semantic SEO data.">
        
        <meta property="og:title" content="AI Readiness & SEO Diagnostic | Blynex Solution">
        <meta property="og:description" content="Check if AI agents can cite your brand. Free semantic code fixes and on-page SEO insights.">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://blynexsolution.com/">
        
        <link rel="icon" href="https://blynexsolution.com/wp-content/uploads/2026/04/Site-Favicon-150x150.png" sizes="32x32">
        <link rel="canonical" href="https://blynexsolution.com/">
        
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Red+Hat+Text:wght@400;600;700;800&display=swap" rel="stylesheet">

        <style>
            body { font-family: 'Red Hat Text', 'Inter', sans-serif; background-color: #090a16; color: #ffffff; }
            .blynex-btn {
                background: linear-gradient(135deg, rgba(17, 17, 114, 0.95) 0%, rgba(26, 26, 255, 0.85) 100%) !important;
                backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.22) !important;
                box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.35), 0 4px 20px rgba(26, 26, 255, 0.3) !important;
                transition: all 0.3s cubic-bezier(.25,1,.5,1) !important;
            }
            .blynex-btn:hover {
                background: linear-gradient(135deg, rgba(26, 26, 255, 0.95) 0%, rgba(58, 58, 255, 0.9) 100%) !important;
                transform: translateY(-2px); box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.5), 0 8px 28px rgba(26, 26, 255, 0.5) !important;
            }
            .blynex-card { background: rgba(18, 20, 43, 0.65); backdrop-filter: blur(14px); border: 1px solid rgba(255, 255, 255, 0.1); }
            .blynex-glow { text-shadow: 0 0 20px rgba(26, 26, 255, 0.6); }
        </style>
    </head>
    <body class="min-h-screen flex flex-col justify-between">
        
        <header class="container mx-auto px-4 md:px-6 py-5 md:py-6 border-b border-white/10" role="banner">
            <nav class="flex justify-between items-center" aria-label="Main Navigation">
                <a href="https://blynexsolution.com/" aria-label="Blynex Solution Home">
                    <img src="https://blynexsolution.com/wp-content/uploads/2026/04/Site-Logo-01.svg" alt="Blynex Solution Logo" class="h-8 md:h-10">
                </a>
                <a href="https://blynexsolution.com/contact/" class="blynex-btn hidden md:inline-block px-6 py-2.5 rounded-md font-semibold text-xs tracking-widest uppercase">TALK TO AN ENGINEER</a>
            </nav>
        </header>

        <main class="container mx-auto px-4 py-10 md:py-16 my-auto" role="main">
            <section class="max-w-4xl mx-auto text-center">
                <p class="text-[10px] md:text-xs font-extrabold tracking-widest uppercase text-indigo-400 mb-3">AI Discovery & Semantic SEO Diagnostic Engine</p>
                <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-4 md:mb-6 leading-tight">Is Your Website <br class="md:hidden"><span class="text-indigo-400 blynex-glow">AI Ready?</span></h1>
                <p class="text-base md:text-xl text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">Check if ChatGPT, Claude, and Perplexity can index your site. Discover target keywords you are ranking for and get custom technical code fixes.</p>

                <form id="auditForm" onsubmit="submitScan(event)" class="max-w-md mx-auto space-y-4" aria-label="Website Audit Form">
                    <div>
                        <label for="url" class="sr-only">Website URL</label>
                        <input type="url" id="url" name="url" placeholder="https://yourwebsite.com" required aria-required="true" class="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 text-base md:text-lg">
                    </div>
                    <div>
                        <label for="email" class="sr-only">Business Email</label>
                        <input type="email" id="email" name="email" placeholder="Enter your business email" required aria-required="true" class="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 text-base md:text-lg">
                    </div>
                    <button type="submit" id="btnText" class="w-full blynex-btn py-4 rounded-xl font-bold uppercase tracking-wider text-sm">RUN SEMANTIC DIAGNOSTIC</button>
                </form>

                <!-- ADVANCED REPORT DASHBOARD -->
                <div id="resultsCard" class="hidden mt-12 text-left space-y-6 md:space-y-8" aria-live="polite">
                    
                    <!-- 1. SCORE OVERVIEW -->
                    <article class="p-6 md:p-8 blynex-card rounded-2xl shadow-2xl">
                        <header class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-white/10 pb-6 gap-4">
                            <div>
                                <h2 id="resTitle" class="text-xl md:text-2xl font-bold text-white"></h2>
                                <p id="resUrl" class="text-indigo-400 text-sm font-mono mt-1 break-all"></p>
                            </div>
                            <div class="text-center bg-indigo-950/70 border border-indigo-500/40 px-6 md:px-8 py-3 rounded-xl w-full md:w-auto">
                                <span id="resScore" class="text-3xl md:text-4xl font-extrabold text-indigo-400"></span>
                                <span class="block text-[10px] md:text-xs uppercase tracking-wider text-slate-400 mt-0.5">AI Indexing Score</span>
                            </div>
                        </header>
                        <div id="resChecks" class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mt-6"></div>
                    </article>

                    <!-- 2. ON-PAGE SEO & TARGETED KEYWORDS DASHBOARD -->
                    <article class="p-6 md:p-8 blynex-card rounded-2xl shadow-2xl border-emerald-500/20">
                        <header>
                            <h3 class="text-lg md:text-xl font-bold text-white mb-4 md:mb-6 flex items-center gap-2"><span>🔍</span> Currently Targeted Keywords & Content Topics</h3>
                        </header>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                            <div class="bg-black/40 p-4 md:p-5 rounded-xl border border-white/5 md:col-span-2">
                                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-2">Primary Keywords & Headlines Detected On Your Site:</p>
                                <div id="seoKeywords" class="space-y-2"></div>
                            </div>
                            <div class="bg-black/40 p-4 md:p-5 rounded-xl border border-white/5 flex justify-between items-center md:col-span-2">
                                <div>
                                    <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Heading Tags Count</p>
                                    <p class="text-white text-sm"><span id="seoH1" class="font-bold text-indigo-300 text-base md:text-lg"></span> H1 Tags found &nbsp;|&nbsp; <span id="seoH2" class="font-bold text-indigo-300 text-base md:text-lg"></span> H2 Tags found</p>
                                </div>
                                <div id="h1Warning" class="text-xl md:text-2xl"></div>
                            </div>
                            <div class="md:col-span-2 bg-black/40 p-4 md:p-5 rounded-xl border border-white/5">
                                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Meta Title</p>
                                <p id="seoTitle" class="text-white text-sm font-medium"></p>
                            </div>
                            <div class="md:col-span-2 bg-black/40 p-4 md:p-5 rounded-xl border border-white/5">
                                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Meta Description</p>
                                <p id="seoDesc" class="text-slate-300 text-sm leading-relaxed"></p>
                            </div>
                        </div>
                    </article>

                    <!-- 3. ACTIONABLE FIXES & TEMPLATES -->
                    <article class="p-6 md:p-8 blynex-card rounded-2xl shadow-2xl">
                        <header>
                            <h3 class="text-lg md:text-xl font-bold text-white mb-2 flex items-center gap-2"><span>⚡</span> Technical Solutions & Code Snippets</h3>
                            <p class="text-slate-400 text-xs md:text-sm mb-6">Deploy these customized files to resolve missing AI protocol warnings immediately.</p>
                        </header>
                        <div id="resFixes" class="space-y-4 md:space-y-6"></div>

                        <div class="mt-8 pt-6 border-t border-white/10 text-center">
                            <p class="text-xs md:text-sm text-slate-300 mb-4">Want the Blynex engineering team to architect your semantic SEO and AI frameworks?</p>
                            <a href="https://blynexsolution.com/contact/" target="_blank" class="blynex-btn block md:inline-block w-full md:w-auto px-6 md:px-8 py-3.5 rounded-lg font-bold text-[10px] md:text-xs uppercase tracking-widest">SCHEDULE AN ENGINEERING CALL</a>
                        </div>
                    </article>

                </div>
            </section>
        </main>

        <footer class="border-t border-white/10 bg-[#060710] py-10 md:py-12 mt-8 md:mt-12" role="contentinfo">
            <div class="container mx-auto px-4 md:px-6 text-center">
                <a href="https://blynexsolution.com/" class="inline-block mb-4" aria-label="Blynex Solution Home">
                    <img src="https://blynexsolution.com/wp-content/uploads/2026/04/Blynex-Footer-Logo.png" alt="Blynex" class="h-10 md:h-12 mx-auto">
                </a>
                <p class="text-slate-400 text-xs md:text-sm max-w-xl mx-auto mb-6 leading-relaxed">Blynex Solution builds high-performance web engineering, digital trust architectures, and semantic SEO systems for businesses globally.</p>
                <nav aria-label="Footer Navigation" class="flex flex-wrap justify-center gap-4 md:gap-6 text-xs md:text-sm text-slate-400">
                    <a href="https://blynexsolution.com/services/" class="hover:text-white transition-colors">Services</a>
                    <a href="https://blynexsolution.com/work/" class="hover:text-white transition-colors">Work</a>
                    <a href="https://blynexsolution.com/contact/" class="hover:text-white transition-colors">Contact</a>
                </nav>
            </div>
        </footer>

        <script>
            async function submitScan(e) {
                e.preventDefault();
                const btn = document.getElementById('btnText');
                const resultsCard = document.getElementById('resultsCard');
                
                btn.innerText = 'ANALYZING DOMAIN & KEYWORDS...';
                btn.disabled = true;

                const formData = new FormData(document.getElementById('auditForm'));

                try {
                    const response = await fetch('/api/scan', { method: 'POST', body: formData });
                    const data = await response.json();

                    // Render Basic Info
                    document.getElementById('resTitle').innerText = data.brand_name.toUpperCase();
                    document.getElementById('resUrl').innerText = data.domain;
                    document.getElementById('resScore').innerText = data.score + '%';

                    // 1. Render Technical Diagnostic
                    document.getElementById('resChecks').innerHTML = `
                        <div class="flex justify-between items-center p-3 md:p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-xs md:text-sm font-medium">LLMs.txt Protocol</span>
                            <span class="${data.results.llms_txt.found ? 'text-emerald-400' : 'text-rose-400'} font-bold text-[10px] md:text-xs uppercase tracking-wider">${data.results.llms_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 md:p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-xs md:text-sm font-medium">Agents.json Config</span>
                            <span class="${data.results.agents_json.found ? 'text-emerald-400' : 'text-rose-400'} font-bold text-[10px] md:text-xs uppercase tracking-wider">${data.results.agents_json.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 md:p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-xs md:text-sm font-medium">AI Crawler Access</span>
                            <span class="${data.results.robots_txt.allowed ? 'text-emerald-400' : 'text-rose-400'} font-bold text-[10px] md:text-xs uppercase tracking-wider">${data.results.robots_txt.status}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 md:p-4 bg-black/40 rounded-xl border border-white/5">
                            <span class="text-xs md:text-sm font-medium">Schema JSON-LD</span>
                            <span class="${data.results.schema_markup.count > 0 ? 'text-emerald-400' : 'text-rose-400'} font-bold text-[10px] md:text-xs uppercase tracking-wider">${data.results.schema_markup.status}</span>
                        </div>
                    `;

                    // 2. Render Targeted Keywords
                    const keywordsContainer = document.getElementById('seoKeywords');
                    if (data.seo_data.targeted_keywords && data.seo_data.targeted_keywords.length > 0) {
                        keywordsContainer.innerHTML = data.seo_data.targeted_keywords.map(kw => `
                            <div class="flex items-center gap-2 text-xs md:text-sm text-emerald-400 font-medium bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-500/20">
                                <span>🎯</span> <span>"${kw}"</span>
                            </div>
                        `).join('');
                    } else {
                        keywordsContainer.innerHTML = `<div class="text-slate-400 text-xs">General Informational Content</div>`;
                    }

                    document.getElementById('seoTitle').innerText = data.seo_data.title;
                    document.getElementById('seoDesc').innerText = data.seo_data.meta_desc;
                    document.getElementById('seoH1').innerText = data.seo_data.h1_count;
                    document.getElementById('seoH2').innerText = data.seo_data.h2_count;
                    
                    const h1Warning = document.getElementById('h1Warning');
                    if(data.seo_data.h1_count === 1) {
                        h1Warning.innerHTML = '✅';
                    } else if(data.seo_data.h1_count === 0) {
                        h1Warning.innerHTML = '❌';
                    } else {
                        h1Warning.innerHTML = '⚠️';
                    }

                    // 3. Render Solutions & Code Fixes
                    const fixesContainer = document.getElementById('resFixes');
                    if (data.fixes.length === 0) {
                        fixesContainer.innerHTML = `<p class="text-emerald-400 text-sm font-semibold p-4 bg-emerald-900/20 rounded-lg border border-emerald-500/30">🎉 All core AI protocol checks passed perfectly! No technical fixes required.</p>`;
                    } else {
                        fixesContainer.innerHTML = data.fixes.map(fix => `
                            <div class="p-4 md:p-5 bg-black/50 rounded-xl border border-white/10 space-y-2 md:space-y-3">
                                <h4 class="text-white font-bold text-sm md:text-base flex items-center gap-2"><span class="text-amber-400">⚠️</span> ${fix.title}</h4>
                                <p class="text-slate-300 text-xs md:text-sm leading-relaxed"><strong>Issue:</strong> ${fix.problem}</p>
                                <p class="text-indigo-300 text-xs md:text-sm font-medium leading-relaxed"><strong>Solution:</strong> ${fix.solution}</p>
                                ${fix.code ? `<div class="mt-3 md:mt-4"><div class="text-[10px] md:text-xs text-slate-400 mb-1 font-mono">Tailored Code Template:</div><pre class="bg-slate-950 p-3 md:p-4 rounded-lg text-emerald-400 text-[10px] md:text-xs font-mono overflow-x-auto border border-white/5 whitespace-pre-wrap word-break">${fix.code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></div>` : ''}
                            </div>
                        `).join('');
                    }

                    resultsCard.classList.remove('hidden');
                } catch (err) {
                    alert('Error running audit scan. Please verify the URL.');
                } finally {
                    btn.innerText = 'RUN SEMANTIC DIAGNOSTIC';
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
