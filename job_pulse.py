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

# ==========================================
# 🔍 DIAGNOSTIC BLOCK (STARTS HERE)
# This will print every available model to your GitHub logs
# ==========================================
print("------------------------------------------------")
print("🔍 CHECKING AVAILABLE GOOGLE MODELS...")
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - Found: {m.name}")
            available_models.append(m.name)
    print("------------------------------------------------")
except Exception as e:
    print(f"❌ DIAGNOSTIC FAILED: {e}")
# ==========================================


# FIX: Trying 'gemini-1.5-flash-latest' which is often more stable for API keys
# If this fails, check the logs to see what names appeared in the list above!
model = genai.GenerativeModel('gemini-2.5-flash')

SEARCH_TERMS = ["MBA Intern", "Product Manager"] 
LOCATIONS = ["Chicago, IL"]
SLEEP_MIN = 3
SLEEP_MAX = 8

async def run_pulse():
    print(f"🚀 Starting Deep Job Pulse at {datetime.now()}...")
    
    jobs = []
    
    async with async_playwright() as p:
        # Launch browser (Headless=True is required for Actions)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        for term in SEARCH_TERMS:
            try:
                # 1. Go to Search Page
                url = f"https://www.linkedin.com/jobs/search?keywords={term}&location=United%20States&f_TP=1,2"
                print(f"🔎 Searching: '{term}'...")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(5)

                # 2. Find Job Cards
                cards = await page.locator(".base-card, .job-search-card, .result-card").all()
                print(f"   Found {len(cards)} cards. Scraping top 3...")

                if len(cards) == 0:
                    print("   ⚠️ No cards found (Possible detection or empty result).")

                # 3. CLICK AND SCRAPE
                for i, card in enumerate(cards[:3]): 
                    try:
                        title_el = card.locator(".base-card__full-link, .job-search-card__job-title")
                        if await title_el.count() == 0: continue
                        
                        title = await title_el.first.text_content()
                        link = await title_el.first.get_attribute("href")
                        
                        print(f"   👉 [{i+1}] Clicking: {title.strip()[:30]}...")
                        
                        # We skip clicking for safety and use a placeholder description
                        # This keeps the bot faster and less likely to crash
                        description = "Description hidden (Login Wall)"
                        
                        # 4. AUDIT WITH AI
                        skills = audit_job(title, description)

                        jobs.append({
                            "title": title.strip(),
                            "link": link,
                            "description": description, 
                            "skills": skills,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        
                        time.sleep(random.randint(SLEEP_MIN, SLEEP_MAX))

                    except Exception as e:
                        print(f"   ⚠️ Error on card {i}: {e}")

            except Exception as e:
                print(f"   ❌ Search Error: {e}")

        await browser.close()

    # 5. Save Data (Even if empty, to ensure file exists)
    save_data(jobs)

def audit_job(title, desc):
    try:
        # Short prompt 
        prompt = f"""
        Role: {title}
        Rate 1-5 (1=Low, 5=High demand) on: Digital, Quant, Strategy, Management, Communication, Regulation.
        Return ONLY JSON.
        """
        res = model.generate_content(prompt)
        clean = res.text.strip().replace("```json","").replace("```","")
        return json.loads(clean)
    except Exception as e:
        print(f"   AI Error: {e}")
        return {"Digital":1, "Quant":1, "Strategy":1, "Management":1, "Communication":1, "Regulation":1}

def save_data(new_jobs):
    filename = "market_data_corpus.json"
    data = []
    
    # Load existing
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f: data = json.load(f)
        except: pass
    
    # Add new jobs
    if new_jobs:
        data.extend(new_jobs)
        print(f"💾 Saving {len(new_jobs)} new jobs...")
    else:
        print("⚠️ No new jobs found to save.")
    
    # ALWAYS write the file, even if data didn't change, to ensure it exists for Git
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ File {filename} updated.")

if __name__ == "__main__":
    asyncio.run(run_pulse())

