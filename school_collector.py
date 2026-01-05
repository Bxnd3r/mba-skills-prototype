import asyncio
import json
import os
import re
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================================
# VALIDATION HELPER
# ==========================================
def is_successful_scrape(courses):
    """
    Decides if a strategy worked based on data quality.
    Criteria:
    1. Found at least 5 courses.
    2. At least 50% of descriptions are non-empty (> 30 chars).
    """
    if not courses or len(courses) < 5:
        return False
    
    valid_descriptions = sum(1 for c in courses if len(c.get('description', '')) > 30)
    success_rate = valid_descriptions / len(courses)
    
    if success_rate > 0.5:
        return True
    return False

# ==========================================
# STRATEGY 1: STANDARD PARALLEL (Fastest)
# Good for: Standard catalogs with <a> links to new pages.
# ==========================================
async def strategy_standard_parallel(context, url):
    print(f"   🚀 STRATEGY 1: Parallel Tabs (Standard)...")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)

        # Search Clicker
        search_btns = page.locator("button:has-text('Search'), input[type='submit']")
        if await search_btns.count() > 0:
            print("      🖱️ Clicking Search...")
            await search_btns.first.click()
            await page.wait_for_timeout(4000)

        # Harvest Links
        print("      👀 Harvesting links...")
        potential_links = await page.locator("tr td a, .course-list a, .result-item h3 a, .result-title a").all()
        valid_urls = []
        for link in potential_links:
            try:
                href = await link.get_attribute("href")
                if href and len(href) > 5 and "javascript" not in href:
                    if not href.startswith("http"):
                        base = "/".join(url.split("/")[:3]) 
                        if href.startswith("/"): href = base + href
                        else: href = "/".join(url.split("/")[:-1]) + "/" + href
                    valid_urls.append(href)
            except: pass
        
        valid_urls = list(set(valid_urls))
        print(f"      ✅ Found {len(valid_urls)} unique links.")

        # Execute Parallel
        sem = asyncio.Semaphore(5) 
        tasks = []
        
        async def scrape_one(link_url, sem):
            async with sem:
                p = await context.new_page()
                try:
                    await p.goto(link_url, wait_until="domcontentloaded", timeout=15000)
                    
                    # Title Finding
                    real_title = "Unknown"
                    headers = await p.locator("h1, h2, h3").all_inner_texts()
                    ignore = ["CATALOG", "DETAILS", "SCHEDULE", "SEARCH"]
                    for h in headers:
                        if len(h) > 5 and not any(x in h.upper() for x in ignore):
                            real_title = h.strip()
                            break
                    if real_title == "Unknown":
                        t = await p.title()
                        real_title = t.split("-")[0].strip()

                    # Description Finding
                    text = await p.inner_text("body")
                    desc = ""
                    if "DESCRIPTION" in text: desc = text.split("DESCRIPTION")[1][:1500]
                    elif "Overview" in text: desc = text.split("Overview")[1][:1500]
                    else: desc = text[:1500]
                    
                    await p.close()
                    if len(desc.strip()) > 30:
                        return {"course": real_title, "description": desc.strip()}
                except:
                    try: await p.close()
                    except: pass
                return None

        # Run limited batch
        for link_url in valid_urls[:80]: 
            tasks.append(scrape_one(link_url, sem))
        
        results = await asyncio.gather(*tasks)
        courses_found = [r for r in results if r is not None]
        
        await page.close()
        return courses_found
    except Exception:
        return []

# ==========================================
# STRATEGY 2: POPUP CLICKER (Medium)
# Good for: Single Page Apps like IIT (Modals/Popups).
# ==========================================
async def strategy_popup_clicker(context, url):
    print(f"   🚀 STRATEGY 2: Popup Clicker (SPA Mode)...")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)

        # Look for course-like links (e.g. "MBA 500")
        links = page.locator("a")
        count = await links.count()
        print(f"      ✅ Scanning {count} links for popups...")

        for i in range(min(count, 150)):
            try:
                link = links.nth(i)
                txt = await link.inner_text()
                
                # Heuristic: Course codes usually have 3 digits (MBA 101, CS 400)
                if not re.search(r'\d{3}', txt): 
                    continue

                # Click
                await link.click()
                await asyncio.sleep(1) # Wait for popup
                
                # Grab content from any visible popup/modal container
                # We try common class names for modals
                popup_text = await page.locator(".courseblock, .modal, .bubble, .tooltip, #course-details").first.inner_text()
                
                if len(popup_text) > 50:
                    lines = [l.strip() for l in popup_text.split('\n') if l.strip()]
                    title = lines[0]
                    desc = max(lines, key=len)
                    
                    if len(desc) > 30:
                        courses_found.append({"course": title, "description": desc})
                        print(f"         📄 Captured: {title[:20]}...")

                # Dismiss popup (Click body 0,0)
                await page.mouse.click(0, 0)
            except: pass

        await page.close()
        return courses_found
    except Exception:
        return []

# ==========================================
# STRATEGY 3: SESSION DRILL-DOWN (Slowest)
# Good for: Chicago Booth / Legacy sites (Click -> Back -> Click).
# ==========================================
async def strategy_session_drilldown(context, url):
    print(f"   🚀 STRATEGY 3: Session Drill-Down (Linear)...")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)

        # Identify rows that look clickable (starting with digits or course codes)
        # Regex: Start with 3+ digits or 2-4 letters followed by numbers
        row_locator = page.locator("text=/^\\d{3}/") 
        if await row_locator.count() == 0:
             row_locator = page.locator("text=/^[A-Z]{2,4}\\s?\\d{3}/")

        count = await row_locator.count()
        print(f"      ✅ Found {count} potential rows.")

        for i in range(min(count, 40)): # Limit 40 due to slowness
            try:
                # Refresh locator
                rows = page.locator("text=/^\\d{3}/") 
                if await rows.count() == 0: rows = page.locator("text=/^[A-Z]{2,4}\\s?\\d{3}/")
                
                if await rows.count() <= i: break
                
                # Click
                await rows.nth(i).click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                
                # Scrape
                full_text = await page.inner_text("body")
                h1 = "Unknown"
                try: h1 = await page.locator("h1").inner_text()
                except: pass

                desc = ""
                if "DESCRIPTION" in full_text: desc = full_text.split("DESCRIPTION")[1]
                elif "CONTENT" in full_text: desc = full_text.split("CONTENT")[1]
                else: desc = full_text[:1000]

                clean_desc = desc.split("PREREQUISITES")[0].strip()[:1500]
                
                if len(clean_desc) > 30:
                    courses_found.append({"course": h1, "description": clean_desc})
                    print(f"         📄 Captured: {h1[:20]}...")

                # Go Back
                await page.go_back()
                await asyncio.sleep(1)

            except:
                try: await page.goto(url) # Reset
                except: pass

        await page.close()
        return courses_found
    except Exception:
        return []

# ==========================================
# MAIN AUTO-PILOT
# ==========================================
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["text", "url"], required=True)
    parser.add_argument("--input", help="URL", required=False)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    final_courses = []

    if args.mode == "text":
        # ... (Text Mode code remains same as before) ...
        pass

    elif args.mode == "url":
        if not args.input:
            print("❌ Error: URL required")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # --- THE STRATEGY LOOP ---
            strategies = [
                strategy_standard_parallel, # 1. Try Fast
                strategy_popup_clicker,     # 2. Try Popup
                strategy_session_drilldown  # 3. Try Drill-Down
            ]
            
            for strategy in strategies:
                try:
                    results = await strategy(context, args.input)
                    
                    if is_successful_scrape(results):
                        print(f"   🎉 SUCCESS! {strategy.__name__} captured {len(results)} valid courses.")
                        final_courses = results
                        break # Stop trying other strategies
                    else:
                        print(f"   ⚠️ {strategy.__name__} failed validation (found {len(results)}). Retrying...")
                except Exception as e:
                    print(f"   ❌ Strategy Error: {e}")

            await browser.close()

    if not final_courses:
        print("❌ ALL STRATEGIES FAILED. No valid courses found.")
        return

    # SAVE
    os.makedirs("raw_school_data", exist_ok=True)
    safe_name = args.name.lower().replace(' ', '_')
    filename = f"raw_school_data/{safe_name}_curriculum.json"
    
    final_data = {
        "school": args.name,
        "source_url": args.input if args.mode == "url" else "manual_text",
        "date_collected": datetime.now().strftime("%Y-%m-%d"),
        "course_count": len(final_courses),
        "curriculum": final_courses
    }

    with open(filename, "w") as f: json.dump(final_data, f, indent=2)
    print(f"✅ FINAL SUCCESS: Saved {len(final_courses)} courses to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
