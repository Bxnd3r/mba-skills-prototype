import asyncio
import json
import os
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIG ---
SEARCH_TERMS = ["MBA Intern", "Product Manager MBA", "Strategy Intern"]
LOCATIONS = ["Chicago, IL", "United States"]
# Reduced sleep to preventing "hanging" appearances, randomized for safety
SLEEP_MIN = 10 
SLEEP_MAX = 20

async def run_pulse():
    print(f"🚀 Starting Daily Job Pulse at {datetime.now()}...")
    
    jobs = []
    
    async with async_playwright() as p:
        # Launch browser (Headless=True for GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Spoof User Agent to look less like a robot
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        for term in SEARCH_TERMS:
            for loc in LOCATIONS:
                try:
                    print(f"🔎 Searching: '{term}' in '{loc}'...")
                    
                    # Construct URL (LinkedIn Guest Search - no login needed)
                    # We use "people" or "jobs" guest search URL
                    url = f"https://www.linkedin.com/jobs/search?keywords={term}&location={loc}&f_TP=1,2"
                    
                    await page.goto(url, wait_until="domcontentloaded")
                    await asyncio.sleep(5) # Wait for initial load
                    
                    # CHECK FOR CAPTCHA / SECURITY WALL
                    title = await page.title()
                    print(f"   📄 Page Title: {title}")
                    
                    if "Security" in title or "Auth" in title or "Challenge" in title:
                        print("   ⚠️ BLOCKED: LinkedIn detected the robot.")
                        await page.screenshot(path="captcha_block.png")
                        continue # Skip this search

                    # Scrape Job Cards
                    # We look for the standard job card class
                    job_cards = await page.locator(".base-card__full-link").all()
                    
                    print(f"   found {len(job_cards)} job cards.")
                    
                    # Limit to top 5 per search to stay safe
                    for i, card in enumerate(job_cards[:5]):
                        try:
                            title_text = await card.text_content()
                            link = await card.get_attribute("href")
                            
                            if title_text and link:
                                clean_title = title_text.strip()
                                print(f"      👉 Found: {clean_title[:40]}...")
                                
                                jobs.append({
                                    "title": clean_title,
                                    "location": loc,
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "link": link
                                })
                        except Exception as e:
                            print(f"      ⚠️ Card error: {e}")

                    # Random Sleep between searches (not 45s, just 10-20s)
                    sleep_time = random.randint(SLEEP_MIN, SLEEP_MAX)
                    print(f"   💤 Sleeping {sleep_time}s...")
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"   ❌ Search Error: {e}")
                    # Take a screenshot so we can debug later
                    await page.screenshot(path="error_state.png")

        await browser.close()

    print(f"✅ Pulse Complete. Collected {len(jobs)} jobs.")
    
    # Save Data
    if jobs:
        output_file = "market_data_corpus.json"
        # Load existing if available
        existing_data = []
        if os.path.exists(output_file):
            try:
                with open(output_file, "r") as f:
                    existing_data = json.load(f)
            except: pass
        
        # Append new (avoid duplicates)
        existing_links = {j['link'] for j in existing_data}
        new_jobs = [j for j in jobs if j['link'] not in existing_links]
        
        final_data = existing_data + new_jobs
        
        with open(output_file, "w") as f:
            json.dump(final_data, f, indent=2)
        print(f"💾 Saved {len(new_jobs)} new jobs to {output_file}")
    else:
        print("⚠️ No jobs found to save.")

if __name__ == "__main__":
    asyncio.run(run_pulse())
