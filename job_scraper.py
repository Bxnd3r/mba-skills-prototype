import asyncio
import json
import os
import random
import logging
import shutil
import gc
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================================
# CONFIGURATION
# ==========================================
# Save data in the SAME folder as this script (MBA_Project)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

USER_DATA_DIR = os.path.join(BASE_PATH, "indeed_bot_profile") 

JOBS_TO_SCRAPE = 4        
MAX_PAGES_TO_CHECK = 10   
RESTART_INTERVAL = 20     

# Speed Settings (M4 Max is fast, but we need to be human)
MIN_SLEEP = 1.5 
MAX_SLEEP = 3.0

# 3. NOW it is safe to setup Logging
log_file = os.path.join(BASE_PATH, "scraper_log.txt")
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    filemode='a'
)

LOCATIONS = ["Illinois", "United States"]

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

def alert_human():
    print('\a')
    os.system('say "Check scraper"')

# ==========================================
# JANITOR
# ==========================================
def clean_start():
    print("🧹 Running Janitor...")
    try: os.system("pkill -f 'Google Chrome'")
    except: pass
    
    # Clear Cache
    for folder in ["Cache", "Code Cache"]:
        path = os.path.join(USER_DATA_DIR, "Default", folder)
        if os.path.exists(path):
            try: shutil.rmtree(path)
            except: pass

# ==========================================
# DATABASE HELPERS
# ==========================================
def backup_database():
    source = os.path.join(BASE_PATH, "jobs_db.json")
    if os.path.exists(source):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = os.path.join(BASE_PATH, "backups", f"jobs_db_{timestamp}.json")
        if not os.path.exists(os.path.dirname(dest)): os.makedirs(os.path.dirname(dest))
        try: shutil.copy2(source, dest)
        except: pass

def load_db_stats():
    filename = os.path.join(BASE_PATH, "jobs_db.json")
    seen = set()
    today_str = datetime.now().strftime("%Y-%m-%d")
    resume_counts = {}

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            for job in data:
                # Fingerprint for duplicates
                t = job.get('job_title_actual', '').lower().strip()
                c = job.get('company', 'Unknown').lower().strip()
                if t: seen.add(f"{t}|{c}")
                
                # Resume Logic
                if job.get('date_collected') == today_str:
                    term = job.get('term', 'Unknown')
                    loc = job.get('location_searched', 'Unknown')
                    key = f"{term}|{loc}"
                    resume_counts[key] = resume_counts.get(key, 0) + 1
            print(f"🧠 Memory Loaded: {len(seen)} unique jobs.")
        except: pass
    return seen, resume_counts

def save_jobs(new_jobs):
    if not new_jobs: return
    filename = os.path.join(BASE_PATH, "jobs_db.json")
    existing = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: existing = json.load(f)
        except: pass
    try:
        with open(filename, "w", encoding="utf-8") as f: json.dump(existing + new_jobs, f, indent=2)
        logging.info(f"SAVED {len(new_jobs)} jobs.")
    except: pass

# ==========================================
# HUMAN INTERVENTION CHECK
# ==========================================
async def check_for_human_intervention(page):
    try:
        # If we see the job list OR the job description, we are good.
        is_normal = await page.locator(".job_seen_beacon, #jobDescriptionText, .jobsearch-JobList").first.is_visible()
        if is_normal: return 

        print("\n🛑 ROBOT PAUSED. (Page blocked or CAPTCHA)")
        alert_human()
        
        # Wait until human fixes it
        while True:
            if await page.locator(".job_seen_beacon, #jobDescriptionText").first.is_visible():
                print("✅ Resuming...")
                await asyncio.sleep(2) 
                return
            await asyncio.sleep(2)
    except: pass

# ==========================================
# WORKER: SINGLE TAB MODE (CLICK & READ)
# ==========================================
async def run_search_term(page, term, location, seen_fingerprints, jobs_needed):
    collected = []
    encoded_term = term.replace(" ", "+")
    encoded_loc = location.replace(" ", "+").replace(",", "%2C")
    
    # Navigate to Search Page
    url = f"https://www.indeed.com/jobs?q={encoded_term}&l={encoded_loc}&sort=date"
    print(f"🔎 Searching: {term} ({location}) [Need {jobs_needed}]...")
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except: return []

    await check_for_human_intervention(page)
    
    found = 0
    page_num = 1

    while page_num <= MAX_PAGES_TO_CHECK:
        # 1. Scroll slightly to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        await asyncio.sleep(1)
        
        await check_for_human_intervention(page)

        # 2. Find all job cards
        job_cards = await page.locator(".job_seen_beacon, .resultContent, [data-jk]").all()
        
        for card in job_cards:
            if found >= jobs_needed: break
            try:
                # Extract Title/Company from the card first
                t_el = card.locator("h2.jobTitle span").first
                if not await t_el.is_visible(): continue
                title = await t_el.inner_text()
                
                c_el = card.locator("[data-testid='company-name']").first
                company = await c_el.inner_text() if await c_el.is_visible() else "Unknown"
                
                # Check duplicates
                sig = f"{title.lower().strip()}|{company.lower().strip()}"
                if sig in seen_fingerprints: continue 

                # 3. CLICK THE CARD (Stay in same tab)
                # Indeed usually opens a 'Split View' on the right side
                link = card.locator("a, [role='button']").first
                await link.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await link.click()
                
                # 4. Wait for the Description Pane to Load
                # The description usually appears in #jobDescriptionText
                try:
                    await page.wait_for_selector("#jobDescriptionText", timeout=4000)
                    desc = await page.locator("#jobDescriptionText").inner_text()
                    
                    if len(desc) > 50:
                        collected.append({
                            "term": term, 
                            "job_title_actual": title, 
                            "company": company,
                            "location_searched": location, 
                            "description": desc, 
                            "source": "indeed",
                            "date_collected": datetime.now().strftime("%Y-%m-%d")
                        })
                        seen_fingerprints.add(sig)
                        found += 1
                        print(f"   ✅ Found: {title[:35]}...")
                        
                        # Save immediately to be safe
                        save_jobs([collected[-1]])
                        collected.pop() # Remove from memory once saved
                        
                except Exception as e:
                    # If pane didn't open, just move to next
                    pass

                # Sleep to be human
                await asyncio.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
                
            except: pass
        
        if found >= jobs_needed: break
            
        # Next Page Logic
        try:
            nxt = page.locator("[data-testid='pagination-page-next']").first
            if await nxt.is_visible():
                print("   ➡️  Next Page...")
                await nxt.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                await check_for_human_intervention(page)
                page_num += 1
            else: break
        except: break

    return [] # We saved as we went, so return empty list

# ==========================================
# MAIN EXECUTION
# ==========================================
async def main():
    print("🚀 STARTING SINGLE-TAB SCRAPER")
    
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH)
    if not os.path.exists(USER_DATA_DIR): os.makedirs(USER_DATA_DIR)
    
    clean_start()
    backup_database()
    
    # Build Task List
    search_queue = []
    for loc in LOCATIONS:
        for item in SEARCH_CONFIG:
            search_queue.append((item["term"], loc))
    
    seen_fingerprints, resume_counts = load_db_stats()
    
    async with async_playwright() as p:
        
        async def launch():
            print("\n🔄 Launching Browser...")
            c = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                viewport={"width": 1400, "height": 900}
            )
            return c, c.pages[0] if c.pages else await c.new_page()

        context, page = await launch()

        for i, (term, location) in enumerate(search_queue):
            
            # RESUME CHECK
            task_key = f"{term}|{location}"
            done_so_far = resume_counts.get(task_key, 0)
            
            if done_so_far >= JOBS_TO_SCRAPE:
                print(f"⏭️  [Task {i+1}/{len(search_queue)}] SKIPPING: {term} ({location})")
                continue

            print(f"\n⚡️ [Task {i+1}/{len(search_queue)}] STARTING: {term} ({location})")
            
            jobs_needed = JOBS_TO_SCRAPE - done_so_far
            
            # Maintenance Restart
            if i > 0 and i % RESTART_INTERVAL == 0:
                print("♻️  Restarting Browser to clean RAM...")
                await context.close()
                await asyncio.sleep(2)
                context, page = await launch()

            try:
                # We save inside the worker now, so no need to return list
                await run_search_term(page, term, location, seen_fingerprints, jobs_needed)
                
                # Update Resume Count manually
                resume_counts[task_key] = JOBS_TO_SCRAPE # Assume we finished if we pass
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"💥 Error: {e}")
                try: await context.close()
                except: pass
                context, page = await launch()

        await context.close()
        print("\n🏆 ALL TASKS COMPLETED.")

if __name__ == "__main__":
    asyncio.run(main())