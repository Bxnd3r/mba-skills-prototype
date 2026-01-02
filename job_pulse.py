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

# Using the high-tier model you confirmed you have access to
model = genai.GenerativeModel('gemini-2.5-flash')

# Terms optimized for Indeed (URL friendly)
SEARCH_TERMS = ["MBA Intern", "Product Manager"] 
LOCATION = "Chicago, IL" 
SLEEP_MIN = 4
SLEEP_MAX = 10

async def run_pulse():
    print(f"🚀 Starting INDEED Job Pulse at {datetime.now()}...")
    
    jobs = []
    
    async with async_playwright() as p:
        # Launch browser with stealth arguments
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )
        page = await context.new_page()
        
        for term in SEARCH_TERMS:
            try:
                # 1. Construct Indeed URL
                # q = query, l = location
                url = f"https://www.indeed.com/jobs?q={term}&l={LOCATION}"
                print(f"🔎 Searching Indeed for: '{term}'...")
                
                await page.goto(url, wait_until="domcontentloaded")
                # Indeed sometimes does a "Verify you are human" check.
                # We wait a bit to let any redirects happen.
                await asyncio.sleep(8) 

                # 2. Find Job Cards (Indeed uses 'job_seen_beacon' or 'resultContent')
                # We look for the main card container
                cards = await page.locator(".job_seen_beacon, .resultContent").all()
                print(f"   Found {len(cards)} cards. Scraping top 3...")

                for i, card in enumerate(cards[:3]): 
                    try:
                        # 3. Extract Details
                        # Title is usually inside a span with id starting with 'jobTitle' or class 'jcs-JobTitle'
                        title_el = card.locator("h2.jobTitle span, .jcs-JobTitle")
                        
                        if await title_el.count() == 0: 
                            print(f"   ⚠️ Skipping card {i}: No title found.")
                            continue
                        
                        title = await title_el.first.text_content()
                        
                        # Indeed links are often complex; we try to grab the anchor tag parent
                        link_el = card.locator("a.jcs-JobTitle, a.jobtitle")
                        if await link_el.count() > 0:
                            raw_link = await link_el.first.get_attribute("href")
                            link = f"https://www.indeed.com{raw_link}" if raw_link.startswith("/") else raw_link
                        else:
                            link = url # Fallback to search page if link fails

                        # 4. THE SNIPPET HACK (Indeed's version)
                        # Indeed puts the summary in '.css-...' classes or '.job-snippet'
                        snippet_el = card.locator(".job-snippet, .underShelfFooter")
                        if await snippet_el.count() > 0:
                            raw_text = await snippet_el.first.text_content()
                            description = raw_text.strip().replace("\n", " ")
                        else:
                            description = "No description preview available."

                        print(f"   👉 [{i+1}] Scraped: {title.strip()[:30]}... | Snippet: {description[:30]}...")
                        
                        # 5. AUDIT WITH AI
                        skills = audit_job(title, description)

                        jobs.append({
                            "source": "Indeed",
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

    save_data(jobs)

def audit_job(title, desc):
    try:
        # Prompt explicitly asking for a flat structure
        prompt = f"""
        Role: {title}
        Snippet: {desc}
        Rate 1-5 (1=Low, 5=High demand) on: Digital, Quant, Strategy, Management, Communication, Regulation.
        Return ONLY a flat JSON object like: {{"Digital": 5, "Quant": 3}}
        """
        res = model.generate_content(prompt)
        clean = res.text.strip().replace("```json","").replace("```","")
        data = json.loads(clean)
        
        # Flatten if nested
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
        print(f"💾 Saving {len(new_jobs)} new jobs from Indeed...")
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_pulse())


