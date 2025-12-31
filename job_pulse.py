import asyncio
import json
import os
import random
import time
from datetime import datetime
import google.generativeai as genai
from playwright.async_api import async_playwright

# --- CONFIG ---
# PASTE YOUR API KEY HERE OR USE ENV VAR
api_key = os.environ.get("GOOGLE_API_KEY") 
if api_key: genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

SEARCH_TERMS = ["MBA Intern", "Product Manager"] # Keep list short for safety
LOCATIONS = ["Chicago, IL"]
SLEEP_MIN = 5
SLEEP_MAX = 15

async def run_pulse():
    print(f"🚀 Starting Deep Job Pulse at {datetime.now()}...")
    
    jobs = []
    
    async with async_playwright() as p:
        # headless=True is safer for GitHub Actions
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Spoof User Agent (Look like a real laptop)
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        for term in SEARCH_TERMS:
            try:
                # 1. Go to Search Page
                url = f"https://www.linkedin.com/jobs/search?keywords={term}&location=United%20States&f_TP=1,2"
                print(f"🔎 Searching: '{term}'...")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(5)

                # 2. Find Job Cards
                # LinkedIn changes class names often, so we try a few
                cards = await page.locator(".base-card, .job-search-card").all()
                print(f"   Found {len(cards)} cards. Scraping top 3...")

                # 3. CLICK AND SCRAPE (The "Deep" Part)
                for i, card in enumerate(cards[:3]): # Limit to 3 per term to avoid ban
                    try:
                        # Get Title first
                        title_el = card.locator(".base-card__full-link")
                        if await title_el.count() == 0: continue
                        
                        title = await title_el.text_content()
                        link = await title_el.get_attribute("href")
                        
                        print(f"   👉 [{i+1}] Clicking: {title.strip()[:30]}...")
                        
                        # Click to open details (this might open a new page or modal)
                        await title_el.click()
                        await asyncio.sleep(3) # Wait for load
                        
                        # Try to find the description on the new page/modal
                        # LinkedIn guest view usually puts it in ".show-more-less-html__markup"
                        desc_el = page.locator(".show-more-less-html__markup, .description__text")
                        
                        if await desc_el.count() > 0:
                            description = await desc_el.first.text_content()
                            clean_desc = description.strip()
                        else:
                            clean_desc = "Description hidden by login wall."

                        # 4. AUDIT WITH AI (Get the Stars!)
                        skills = {}
                        if len(clean_desc) > 50:
                            skills = audit_job(title, clean_desc)

                        jobs.append({
                            "title": title.strip(),
                            "link": link,
                            "description": clean_desc[:200] + "...", # Preview only
                            "full_text": clean_desc,
                            "skills": skills,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        
                        # Sleep to act human
                        time.sleep(random.randint(SLEEP_MIN, SLEEP_MAX))

                    except Exception as e:
                        print(f"   ⚠️ Error on card {i}: {e}")

            except Exception as e:
                print(f"   ❌ Search Error: {e}")

        await browser.close()

    # 5. Save Data
    save_data(jobs)

def audit_job(title, desc):
    # Ask Gemini to rate the job
    try:
        prompt = f"""
        Role: {title}
        Desc: {desc[:1000]}
        Rate 1-5 (1=Low, 5=High demand) on: Digital, Quant, Strategy, Management, Communication, Regulation.
        Return ONLY JSON: {{"Digital":X, "Quant":X...}}
        """
        res = model.generate_content(prompt)
        clean = res.text.strip().replace("```json","").replace("```","")
        return json.loads(clean)
    except:
        return {"Digital":1, "Quant":1, "Strategy":1, "Management":1, "Communication":1, "Regulation":1}

def save_data(new_jobs):
    filename = "market_data_corpus.json"
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f: data = json.load(f)
        except: pass
    
    # Add new jobs
    data.extend(new_jobs)
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved {len(new_jobs)} jobs with skills to {filename}")

if __name__ == "__main__":
    asyncio.run(run_pulse())
