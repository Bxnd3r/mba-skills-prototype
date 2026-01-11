import asyncio
import json
import os
import random
import re
import gc
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================================
# CONFIGURATION
# ==========================================
JOBS_TO_SCRAPE = 4      # Goal: Find 4 NEW jobs per term
MAX_PAGES_TO_CHECK = 10 # <--- CHANGED: Will dig up to 10 pages deep
RESTART_EVERY_N_SEARCHES = 3 

LOCATIONS = [
    "Illinois",
    "United States"
]

SEARCH_CONFIG = [
    # --- CORE CONSULTING & STRATEGY ---
    {"term": "Management Consultant", "onet_code": "13-1111.00"},
    {"term": "Strategy Consultant", "onet_code": "13-1111.00"},
    {"term": "Corporate Strategy", "onet_code": "13-1111.00"},
    {"term": "Strategy Manager", "onet_code": "11-1021.00"},
    {"term": "Business Operations", "onet_code": "13-1199.00"},
    {"term": "Chief of Staff", "onet_code": "11-1011.00"},
    {"term": "Strategic Initiatives", "onet_code": "13-1111.00"},

    # --- PROJECT & PRODUCT MANAGEMENT ---
    {"term": "Project Manager", "onet_code": "13-1082.00"},
    {"term": "Program Manager", "onet_code": "13-1082.00"},
    {"term": "Product Manager", "onet_code": "15-1299.09"},
    {"term": "Product Owner", "onet_code": "15-1299.09"},

    # --- FINANCE ---
    {"term": "Financial Analyst", "onet_code": "13-2051.00"},
    {"term": "Investment Analyst", "onet_code": "13-2051.00"},
    {"term": "FP&A Manager", "onet_code": "11-3031.00"},
    {"term": "Finance Manager", "onet_code": "11-3031.00"},
    {"term": "Investment Banking Associate", "onet_code": "13-2099.00"},
    {"term": "Private Equity Associate", "onet_code": "13-2099.00"},

    # --- MARKETING & GROWTH ---
    {"term": "Marketing Manager", "onet_code": "11-2021.00"},
    {"term": "Brand Manager", "onet_code": "11-2021.00"},
    {"term": "Product Marketing Manager", "onet_code": "13-1161.00"},
    {"term": "Growth Marketing Manager", "onet_code": "13-1161.00"},
    {"term": "Go-to-Market Manager", "onet_code": "13-1161.00"},

    # --- SALES & REVENUE OPS ---
    {"term": "Business Development Manager", "onet_code": "11-2022.00"},
    {"term": "Account Executive", "onet_code": "41-3011.00"},
    {"term": "Partnerships Manager", "onet_code": "11-2022.00"},
    {"term": "Revenue Operations", "onet_code": "13-1199.00"},
    {"term": "Sales Operations", "onet_code": "13-1199.00"},
    {"term": "Customer Success Manager", "onet_code": "11-2022.00"},

    # --- OPERATIONS & SUPPLY CHAIN ---
    {"term": "Operations Manager", "onet_code": "11-1021.00"},
    {"term": "Supply Chain Manager", "onet_code": "11-3071.04"},
    {"term": "Procurement Manager", "onet_code": "11-3061.00"},

    # --- HEALTHCARE (MBA Roles) ---
    {"term": "Hospital Administrator", "onet_code": "11-9111.00"},
    {"term": "Healthcare Strategy", "onet_code": "13-1111.00"},
    {"term": "Pharmaceutical Product Manager", "onet_code": "11-2021.00"},
    {"term": "Regional Operations Director", "onet_code": "11-1021.00"},
    {"term": "Practice Administrator", "onet_code": "11-9111.00"},

    # --- DATA & ANALYTICS ---
    {"term": "Business Intelligence Analyst", "onet_code": "15-2051.01"},
    {"term": "Data Analytics Manager", "onet_code": "15-2051.00"},
    {"term": "Business Analyst", "onet_code": "13-1111.00"},

    # --- SPECIALIZED TRACKS ---
    {"term": "Sustainability Manager", "onet_code": "11-1011.03"},
    {"term": "Human Resources Manager", "onet_code": "11-3121.00"},
    {"term": "People Operations", "onet_code": "11-3121.00"},
]

# ==========================================
# HELPER: LOAD MEMORY
# ==========================================
def load_seen_jobs(filename="jobs_db.json"):
    seen = set()
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                for job in data:
                    t = job.get('job_title_actual', '').lower().strip()
                    c = job.get('company', 'Unknown').lower().strip()
                    if t:
                        sig = f"{t}|{c}" 
                        seen.add(sig)
        except: pass
    return seen

# ==========================================
# HELPER: SAVE DATA
# ==========================================
def save_jobs(new_jobs, filename="jobs_db.json"):
    if not new_jobs: return
    
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                existing_data = json.load(f)
        except: pass 
    
    final_list = existing_data + new_jobs
    
    with open(filename, "w") as f:
        json.dump(final_list, f, indent=2)
    print(f"      💾 Saved {len(new_jobs)} jobs to DB.")

# ==========================================
# WORKER: RUN ONE SEARCH (WITH PAGINATION)
# ==========================================
async def run_search_term(page, term, location, seen_fingerprints):
    collected = []
    
    encoded_term = term.replace(" ", "+")
    encoded_loc = location.replace(" ", "+").replace(",", "%2C")
    
    # Start at Page 1 URL
    base_url = f"https://www.indeed.com/jobs?q={encoded_term}&l={encoded_loc}&sort=date"
    
    print(f"   🔎 Searching: {term} in {location}...")
    
    await page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
    
    total_found_for_term = 0
    current_page_num = 1

    # PAGINATION LOOP
    while current_page_num <= MAX_PAGES_TO_CHECK:
        
        # 1. Scroll to load cards
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.0)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

        # 2. Scrape Visible Cards
        job_cards = await page.locator(".job_seen_beacon, .resultContent, [data-jk]").all()
        
        found_on_this_page = 0
        
        for card in job_cards:
            if total_found_for_term >= JOBS_TO_SCRAPE: break

            try:
                # Fingerprint Check
                title_el = card.locator("h2.jobTitle span").first
                company_el = card.locator("[data-testid='company-name']").first
                
                if not await title_el.is_visible(): continue

                title_text = await title_el.inner_text()
                company_text = "Unknown"
                if await company_el.is_visible():
                    company_text = await company_el.inner_text()
                
                current_sig = f"{title_text.lower().strip()}|{company_text.lower().strip()}"
                
                if current_sig in seen_fingerprints:
                    continue # Skip duplicate

                # Click & Capture
                link_el = card.locator("h2.jobTitle a").first
                if await link_el.count() == 0: continue

                await link_el.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await link_el.click(timeout=5000)
                
                try:
                    await page.wait_for_selector("#jobDescriptionText", timeout=4000)
                    desc = await page.locator("#jobDescriptionText").inner_text()
                except: continue 

                full_title = title_text
                t_el = page.locator(".jobsearch-JobInfoHeader-title").first
                if await t_el.is_visible():
                    full_title = await t_el.inner_text()

                if len(desc) > 50:
                    entry = {
                        "term": term, 
                        "job_title_actual": full_title.split('\n')[0],
                        "company": company_text,
                        "location_searched": location,
                        "description": desc,
                        "source": "indeed",
                        "date_collected": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    collected.append(entry)
                    seen_fingerprints.add(current_sig)
                    total_found_for_term += 1
                    found_on_this_page += 1
                    print(f"      ✅ Captured: {full_title[:30]}...")
                
                await asyncio.sleep(random.uniform(1.0, 2.0))

            except Exception: pass
        
        # 3. Decision Time: Next Page or Quit?
        if total_found_for_term >= JOBS_TO_SCRAPE:
            break # Goal met
            
        print(f"      (Page {current_page_num}: Found {found_on_this_page} new. Total: {total_found_for_term}/{JOBS_TO_SCRAPE})")
        
        # Try to find "Next Page" button
        try:
            # Indeed's Next Button usually has data-testid="pagination-page-next"
            next_btn = page.locator("[data-testid='pagination-page-next']").first
            
            if await next_btn.is_visible():
                print("      ➡️ Clicking Next Page...")
                await next_btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3) # Wait for load
                current_page_num += 1
                
                # Close potential "Email Popup" if it appears on page 2
                try:
                    close_popup = page.locator("button[aria-label='close']").first
                    if await close_popup.is_visible():
                        await close_popup.click()
                except: pass
                
            else:
                print("      🛑 No more pages.")
                break
        except:
            break # Error finding next button

    if total_found_for_term == 0:
        print("      (No new unique jobs found after checking pages)")
        
    return collected

# ==========================================
# MAIN: SELF-HEALING LOOP
# ==========================================
async def main():
    print("🕵️  Launching Job Collector (Deep Dig 10 Pages)...")
    
    search_queue = []
    for loc in LOCATIONS:
        for item in SEARCH_CONFIG:
            search_queue.append((item["term"], loc))
    
    print(f"📋 Task List: {len(search_queue)} searches queued.")
    seen_fingerprints = load_seen_jobs("jobs_db.json")
    print(f"🧠 Memory Loaded: Remembering {len(seen_fingerprints)} past jobs.")

    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        
        async def launch_browser():
            gc.collect() 
            print("\n🔄 (Re)Launching Browser...")
            # HEADLESS=TRUE IS CRITICAL FOR BACKGROUND TASK
            b = await p.chromium.launch(
                headless=True, # <--- KEEP THIS TRUE FOR TASK SCHEDULER
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            c = await b.new_context(viewport={"width": 1280, "height": 800})
            await c.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            pg = await c.new_page()
            return b, c, pg

        browser, context, page = await launch_browser()
        
        queue_index = 0
        searches_since_restart = 0

        while queue_index < len(search_queue):
            term, location = search_queue[queue_index]
            
            if searches_since_restart >= RESTART_EVERY_N_SEARCHES:
                print("🧹 Cleaning memory...")
                try: await browser.close()
                except: pass
                gc.collect() 
                browser, context, page = await launch_browser()
                searches_since_restart = 0

            try:
                print(f"\n[{queue_index+1}/{len(search_queue)}] Progress...")
                new_jobs = await run_search_term(page, term, location, seen_fingerprints)
                save_jobs(new_jobs)
                queue_index += 1
                searches_since_restart += 1
                gc.collect()
            
            except Exception as e:
                print(f"\n💥 CRASH: {e}")
                try: await browser.close()
                except: pass
                await asyncio.sleep(5)
                browser, context, page = await launch_browser()
                searches_since_restart = 0

        await browser.close()
        print("\n🏆 ALL TASKS COMPLETED.")

if __name__ == "__main__":
    asyncio.run(main())