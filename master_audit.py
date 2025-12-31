import asyncio
import json
import os
import random
import time
import sys  # <--- CRITICAL IMPORT FOR GITHUB ACTIONS
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- 1. CONFIGURATION ---
# We check if the key exists to avoid crashing locally if you forget it
api_key = os.environ.get("AIzaSyC_fQtJV9MD4RFikgQGga4CRWZJrAkaFEg")
if api_key:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-pro')

DEFAULT_RECIPE = {
    "block": ".courseblock, .course-item, div[class*='course']", 
    "title": "strong, .courseblocktitle, h3", 
    "desc": ".courseblockdesc, .description"
}

# --- 2. SCRAPER ---
async def universal_scrape(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"🕵️ Scraping {url}...")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        courses = parse_html(soup)
    except:
        courses = []

    if not courses:
        print("⚠️ Static failed. Launching Playwright...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            content = await page.content()
            courses = parse_html(BeautifulSoup(content, "html.parser"))
            await browser.close()
    return courses

def parse_html(soup):
    results = []
    blocks = soup.select(DEFAULT_RECIPE["block"])
    for b in blocks:
        t = b.select_one(DEFAULT_RECIPE["title"])
        d = b.select_one(DEFAULT_RECIPE["desc"])
        if t and d:
            title = t.get_text(strip=True).replace('\u00a0', ' ')
            desc = d.get_text(strip=True)
            if len(desc) > 30:
                results.append({"course": title, "text": desc})
    return results

# --- 3. AUDITOR ---
async def audit_with_gemini(course_list):
    print(f"🧠 Auditing {len(course_list)} courses...")
    audited = []
    prompt = """
    Score this MBA course 1-5 on: Digital, Quant, Strategy, Management, Communication, Regulation.
    Rubric: 1=Awareness (Brief mention), 3=Application (Labs/Case Studies), 5=Mastery (Capstone/Client Project).
    Course: {name} | Desc: {desc}
    Return ONLY JSON: {{"Digital":X, "Quant":X, "Strategy":X, "Management":X, "Communication":X, "Regulation":X}}
    """
    
    for i, c in enumerate(course_list):
        print(f"📝 [{i+1}/{len(course_list)}] {c['course'][:30]}...")
        retries = 0
        while retries < 3:
            try:
                response = model.generate_content(prompt.format(name=c['course'], desc=c['text']))
                raw = response.text.strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                audited.append({"course": c['course'], "skills": json.loads(raw), "text": c['text']})
                time.sleep(2)
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"⏳ Rate Limit! Sleeping 60s...")
                    time.sleep(60)
                    retries += 1
                else:
                    print(f"⚠️ Error: {e}")
                    break
    return audited

# --- 4. REGISTRY ---
def update_registry(school_id, name, filename):
    reg_path = "registry.json"
    registry = []
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r") as f: registry = json.load(f)
        except: registry = []

    # Update or Add
    existing = next((item for item in registry if item["id"] == school_id), None)
    if existing:
        existing["audit"] = filename # Update existing entry
    else:
        registry.append({
            "id": school_id, 
            "name": name, 
            "audit": filename, 
            "color": f"rgba({random.randint(50,200)},{random.randint(50,200)},255,1)"
        })
    
    with open(reg_path, "w") as f: json.dump(registry, f, indent=2)
    print(f"📖 Registry saved.")

# --- 5. EXECUTION ---
async def run_pipeline(url, name):
    domain = urlparse(url).netloc.split('.')
    school_id = domain[1] if domain[0] in ['www', 'catalog'] else domain[0]
    
    courses = await universal_scrape(url)
    
    # CRITICAL FIX: Fail loudly if no courses found
    if not courses: 
        print(f"❌ ERROR: No courses found at {url}")
        sys.exit(1) # This stops the workflow immediately so you see the error

    audited = await audit_with_gemini(courses)
    
    filename = f"{school_id}_audit.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(audited, f, indent=2)
    
    update_registry(school_id, name, filename)
    print(f"✅ SUCCESS! Created {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(run_pipeline(sys.argv[1], sys.argv[2]))
    else:
        # Local test mode
        asyncio.run(run_pipeline("[https://catalog.iit.edu/courses/mba/](https://catalog.iit.edu/courses/mba/)", "IIT Stuart School of Business"))
