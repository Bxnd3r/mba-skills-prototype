import asyncio
import json
import os
import random
import time
from datetime import datetime
import google.generativeai as genai
from playwright.async_api import async_playwright

# --- CONFIG ---
api_key = os.environ.get("GOOGLE_API_KEY") 
if api_key: genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

SEARCH_TERMS = ["MBA Intern", "Product Manager"] 
LOCATION = "Chicago, IL" 
SLEEP_MIN = 4
SLEEP_MAX = 10

async def run_pulse():
    print(f"🚀 Starting INDEED (Stealth Mode) at {datetime.now()}...")
    
    jobs = []
    
    async with async_playwright() as p:
        # --- THE STEALTH FIX ---
        # We add arguments to hide the "Automation" flag
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        # Extra script to delete the "I am a robot" property from the browser
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        for term in SEARCH_TERMS:
            try:
                url = f"https://www.indeed.com/jobs?q={term}&l={LOCATION}"
                print(f"🔎 Searching: '{term}'...")
                
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(8) 

                # Debug: Print page title to see if we were blocked
                title = await page.title()
                print(f"   (Page Title: {title})")

                # Try finding cards
                cards = await page.locator(".job_seen_beacon, .resultContent").all()
                print(f"   Found {len(cards)} cards...")

                for i, card in enumerate(cards[:3]): 
                    try:
                        title_el = card.locator("h2.jobTitle span, .jcs-JobTitle")
                        if await title_el.count() == 0: continue
                        
                        title = await title_el.first.text_content()
                        
                        # Snippet logic
                        snippet_el = card.locator(".job-snippet, .underShelfFooter")
                        if await snippet_el.count() > 0:
                            desc = await snippet_el.first.text_content()
                            desc = desc.strip().replace("\n", " ")
                        else:
                            desc = "No preview available."

                        # Link logic
                        link_el = card.locator("a.jcs-JobTitle, a.jobtitle")
                        if await link_el.count() > 0:
                            raw_link = await link_el.first.get_attribute("href")
                            link = f"https://www.indeed.com{raw_link}" if raw_link.startswith("/") else raw_link
                        else:
                            link = url

                        print(f"   👉 [{i+1}] Scraped: {title.strip()[:30]}...")

                        skills = audit_job(title, desc)
                        jobs.append({
                            "source": "Indeed",
                            "title": title.strip(),
                            "link": link,
                            "description": desc, 
                            "skills": skills,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        time.sleep(random.randint(SLEEP_MIN, SLEEP_MAX))

                    except Exception as e:
                        print(f"   ⚠️ Error on card {i}: {e}")

            except Exception as e:
                print(f"   ❌ Search Error: {e}")

        await browser.close()

    save_data(jobs)

def audit_job(title, desc):
    try:
        prompt = f"""
        Role: {title}
        Snippet: {desc}
        Rate 1-5 (1=Low, 5=High demand) on: Digital, Quant, Strategy, Management, Communication, Regulation.
        Return ONLY a flat JSON object like: {{"Digital": 5, "Quant": 3}}
        """
        res = model.generate_content(prompt)
        clean = res.text.strip().replace("```json","").replace("```","")
        data = json.loads(clean)
        if data and isinstance(list(data.values())[0], dict):
            data = list(data.values())[0]
        return data
    except:
        return {"Digital":1, "Quant":1, "Strategy":1, "Management":1, "Communication":1, "Regulation":1}

def save_data(new_jobs):
    filename = "market_data_corpus.json"
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f: data = json.load(f)
        except: pass
    
    if new_jobs:
        data.extend(new_jobs)
        print(f"💾 Saving {len(new_jobs)} new jobs...")
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_pulse())
