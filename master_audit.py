import asyncio
import json
import os
import random
import time
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- 1. CONFIGURATION ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Use Flash model for speed/cost
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. SCHOOL RECIPES (The Dictionary) ---
SCHOOL_RECIPES = {
    "default": {
        "block": ".courseblock, .course-item, div[class*='course'], li[class*='course']", 
        "title": "strong, .courseblocktitle, h3, .course-title", 
        "desc": ".courseblockdesc, .description, .course-desc"
    },
    # BOOTH SPECIFIC RECIPE (Now properly inside the dictionary)
    "chicagobooth": {
        "block": "tr, div.course-listing, li.course-item", 
        "title": "td:nth-child(1), h4, strong.course-title, .course-name",
        "desc": "td:nth-child(2), div.description, p, .course-description"
    }
}

# --- 3. SCRAPER ENGINE ---
async def universal_scrape(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Detect School from URL to pick the right Recipe
    domain = urlparse(url).netloc
    recipe_key = "default"
    for key in SCHOOL_RECIPES:
        if key in domain:
            recipe_key = key
            break
            
    print(f"🕵️ Scraping {url} using recipe: {recipe_key.upper()}...")
    recipe = SCHOOL_RECIPES[recipe_key]

    # 2. Try Static Scrape First
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        courses = parse_html(soup, recipe)
    except:
        courses = []

    # 3. Failover to Dynamic (Playwright) if static failed
    if not courses:
        print("⚠️ Static failed. Launching Playwright...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(5) # Wait for JS to load
                content = await page.content()
                courses = parse_html(BeautifulSoup(content, "html.parser"), recipe)
            except Exception as e:
                print(f"❌ Playwright Error: {e}")
            await browser.close()
            
    return courses

def parse_html(soup, recipe):
    results = []
    blocks = soup.select(recipe["block"])
    print(f"🔎 Found {len(blocks)} potential course blocks...")
    
    for b in blocks:
        t = b.select_one(recipe["title"])
        d = b.select_one(recipe["desc"])
        
        # If we found a title but no description, try getting all text in the block
        if t:
            title = t.get_text(strip=True).replace('\u00a0', ' ')
            if d:
                desc = d.get_text(strip=True)
            else:
                # Fallback: Use the whole block text minus the title
                desc = b.get_text(strip=True).replace(title, "")
            
            # Clean up noise
            if len(desc) > 20: 
                results.append({"course": title, "text": desc})
                
    return results

# --- 4. AUDITOR ENGINE ---
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

# --- 5. REGISTRY UPDATER ---
def update_registry(school_id, name, filename):
    reg_path = "registry.json"
    registry = []
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r") as f: registry = json.load(f)
        except: registry = []

    # Update or Add
    existing = next((item for item in registry if item["id"] == school_id), None)
