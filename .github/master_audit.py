import asyncio
import json
import os
import random
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- 1. SETUP & CONFIG ---
# PASTE YOUR KEY HERE
genai.configure(api_key="AIzaSyC_fQtJV9MD4RFikgQGga4CRWZJrAkaFEg") 

# UPDATED: Use the faster, stable Flash model
model = genai.GenerativeModel('gemini-pro')

DEFAULT_RECIPE = {
    "block": ".courseblock, .course-item, div[class*='course']", 
    "title": "strong, .courseblocktitle, h3", 
    "desc": ".courseblockdesc, .description"
}

# --- 2. THE SCRAPER ENGINE (Hybrid) ---
async def universal_scrape(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"🕵️ Attempting static scrape for {url}...")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        courses = parse_html(soup)
    except:
        courses = []

    if not courses:
        print("⚠️ Static failed. Launching Playwright Failsafe...")
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

# --- 3. THE GEMINI AUDITOR (Robust with Retry) ---
async def audit_with_gemini(course_list):
    print(f"🧠 Auditing {len(course_list)} courses with Gemini...")
    audited = []
    prompt = """
    Score this MBA course 1-5 on: Digital, Quant, Strategy, Management, Communication, Regulation.
    Rubric: 1=Awareness (Brief mention), 3=Application (Labs/Case Studies), 5=Mastery (Capstone/Client Project).
    Course: {name} | Desc: {desc}
    Return ONLY JSON: {{"Digital":X, "Quant":X, "Strategy":X, "Management":X, "Communication":X, "Regulation":X}}
    """
    
    for i, c in enumerate(course_list):
        print(f"📝 Auditing [{i+1}/{len(course_list)}]: {c['course'][:30]}...")
        retries = 0
        while retries < 3:
            try:
                response = model.generate_content(prompt.format(name=c['course'], desc=c['text']))
                raw = response.text.strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                
                scores = json.loads(raw)
                audited.append({"course": c['course'], "skills": scores, "text": c['text']})
                time.sleep(2) # Safety pause
                break
            except Exception as e:
                if "429" in str(e) or "Quota" in str(e):
                    print(f"⏳ Rate Limit! Sleeping 60s...")
                    time.sleep(60)
                    retries += 1
                else:
                    print(f"⚠️ Error: {e}")
                    break
    return audited

# --- 4. THE REGISTRY UPDATER (Safe) ---
def update_registry(school_id, name, filename):
    reg_path = "registry.json"
    registry = []
    
    # Safe Load
    if os.path.exists(reg_path) and os.path.getsize(reg_path) > 0:
        try:
            with open(reg_path, "r") as f: registry = json.load(f)
        except: registry = []

    if not any(s['id'] == school_id for s in registry):
        registry.append({
            "id": school_id, 
            "name": name, 
            "audit": filename, 
            "color": f"rgba({random.randint(50,200)},{random.randint(50,200)},255,1)"
        })
        with open(reg_path, "w") as f: json.dump(registry, f, indent=2)
        print(f"📖 Registry Updated with {name}")

# --- 5. THE MASTER FLOW ---
async def run_pipeline(url, school_display_name):
    print(f"🚀 Starting Pipeline for: {school_display_name}")
    
    # 1. Get ID
    domain = urlparse(url).netloc.split('.')
    school_id = domain[1] if domain[0] in ['www', 'catalog'] else domain[0]
    
    # 2. Scrape
    raw_courses = await universal_scrape(url)
    if not raw_courses: return print("❌ No courses found.")
    print(f"✅ Found {len(raw_courses)} courses.")

    # 3. Audit
    audited_data = await audit_with_gemini(raw_courses)
    
    # 4. Save
    filename = f"{school_id}_audit.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(audited_data, f, indent=2)
    
    # 5. Register
    update_registry(school_id, school_display_name, filename)
    print(f"🏁 DONE! Added {school_display_name} to the platform.")

# --- EXECUTE ---
# Uncomment the line below to run it!
# GOOD LINE (Clean URL string)
asyncio.run(run_pipeline("https://catalog.iit.edu/courses/mba/", "IIT Stuart School of Business"))