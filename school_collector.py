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
    if not courses or len(courses) < 5:
        return False
    valid_descriptions = sum(1 for c in courses if len(c.get('description', '')) > 30)
    success_rate = valid_descriptions / len(courses)
    return success_rate > 0.5

# ==========================================
# STRATEGY 1: STANDARD PARALLEL (Fastest)
# ==========================================
async def strategy_standard_parallel(context, url):
    print(f"   🚀 STRATEGY 1: Parallel Tabs (Standard)...")
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)

        search_btns = page.locator("button:has-text('Search'), input[type='submit']")
        if await search_btns.count() > 0:
            print("      🖱️ Clicking Search...")
            await search_btns.first.click()
            await page.wait_for_timeout(4000)

        print("      👀 Harvesting links...")
        # Broad selector for anything that looks like a course link
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

        if len(valid_urls) < 5: return [] # Fail fast if no links

        sem = asyncio.Semaphore(5) 
        tasks = []
        
        async def scrape_one(link_url, sem):
            async with sem:
                p = await context.new_page()
                try:
                    await p.goto(link_url, wait_until="domcontentloaded", timeout=15000)
                    
                    real_title = "Unknown"
                    headers = await p.locator("h1, h2, h3").all_inner_texts()
                    ignore = ["CATALOG", "DETAILS", "SCHEDULE", "SEARCH", "RESULTS"]
                    for h in headers:
                        if len(h) > 5 and not any(x in h.upper() for x in ignore):
                            real_title = h.strip()
                            break
                    if real_title == "Unknown":
                        t = await p.title()
                        real_title = t.split("-")[0].strip()

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

        for link_url in valid_urls[:80]: 
            tasks.append(scrape_one(link_url, sem))
        
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    except Exception:
        return []

# ==========================================
# STRATEGY 2: POPUP CLICKER (SPA Mode)
# ==========================================
async def strategy_popup_clicker(context, url):
    print(f"   🚀 STRATEGY 2: Popup Clicker (SPA Mode)...")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3)

        links = page.locator("a")
        count = await links.count()
        print(f"      ✅ Scanning {count} links for popups...")

        for i in range(min(count, 150)):
            try:
                link = links.nth(i)
                txt = await link.inner_text()
                if not re.search(r'\d{3}', txt): continue

                await link.click()
                await asyncio.sleep(1) 
                
                popup_text = await page.locator(".courseblock, .modal, .bubble, .tooltip").first.inner_text()
                
                if len(popup_text) > 50:
                    lines = [l.strip() for l in popup_text.split('\n') if l.strip()]
                    title = lines[0]
                    desc = max(lines, key=len)
                    if len(desc) > 30:
                        courses_found.append({"course": title, "description": desc})

                await page.mouse.click(0, 0)
            except: pass

        await page.close()
        return courses_found
    except Exception:
        return []

# ==========================================
# STRATEGY 3: SESSION DRILL-DOWN (Smart Hunter)
# ==========================================
async def strategy_session_drilldown(context, url):
    print(f"   🚀 STRATEGY 3: Session Drill-Down (Linear)...")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)

        # 1. SMART ROW HUNTER
        # We try multiple regex patterns to find the course list
        patterns = [
            r"^\d{5}\s",          # Booth (5 digits): "30000 - Title"
            r"^\d{5}$",           # Just 5 digits
            r"^[A-Z]{2,4}\s\d{3}", # Standard: "MBA 501"
            r"^\d{3}\s"           # Generic 3 digit
        ]
        
        best_locator = None
        best_count = 0
        
        print("      👀 Testing row patterns...")
        for pattern in patterns:
            loc = page.locator(f"text=/{pattern}/")
            count = await loc.count()
            if count > 3: # If we find more than 3, we assume this is the right pattern
                print(f"         ✅ Match found for pattern '{pattern}': {count} rows")
                best_locator = loc
                best_count = count
                break
        
        if not best_locator:
            print("         ⚠️ No recognizeable rows found.")
            await page.close()
            return []

        # 2. ITERATE
        for i in range(min(best_count, 40)):
            try:
                # Refresh locator (Page DOM changes on back navigation)
                # We re-use the pattern that worked
                rows = page.locator(f"text=/{pattern}/")
                if await rows.count() <= i: break
                
                # Capture title before clicking
                title_preview = await rows.nth(i).inner_text()
                
                # Click
                await rows.nth(i).click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                
                # Scrape
                full_text = await page.inner_text("body")
                h1 = "Unknown"
                try: 
                    # Try to find a header that isn't the page title
                    headers = await page.locator("h1").all_inner_texts()
                    for h in headers:
                         if len(h) > 5 and "CATALOG" not in h.upper():
                             h1 = h
                             break
                except: pass
                
                if h1 == "Unknown": h1 = title_preview # Fallback to list title

                desc = ""
                if "DESCRIPTION" in full_text: desc = full_text.split("DESCRIPTION")[1]
                elif "CONTENT" in full_text: desc = full_text.split("CONTENT")[1]
                else: desc = full_text[:1000]

                clean_desc = desc.split("PREREQUISITES")[0].split("MATERIALS")[0].strip()[:1500]
                
                if len(clean_desc) > 30:
                    courses_found.append({"course": h1, "description": clean_desc})
                    print(f"         📄 Captured: {h1[:30]}...")

                # Go Back
                await page.go_back()
                await asyncio.sleep(1)

            except:
                try: await page.goto(url)
                except: pass

        await page.close()
        return courses_found
    except Exception as e:
        print(f"      ❌ Error: {e}")
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
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                # Simple parser for copy-pasted text
                for line in f:
                    if len(line) > 20: final_courses.append({"course": "Manual", "description": line.strip()})
    
    elif args.mode == "url":
        if not args.input:
            print("❌ Error: URL required")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            strategies = [
                strategy_standard_parallel,
                strategy_session_drilldown, # Moved Drill-Down to 2nd priority for Booth
                strategy_popup_clicker
            ]
            
            for strategy in strategies:
                try:
                    results = await strategy(context, args.input)
                    if is_successful_scrape(results):
                        print(f"   🎉 SUCCESS! {strategy.__name__} captured {len(results)} valid courses.")
                        final_courses = results
                        break 
                    else:
                        print(f"   ⚠️ {strategy.__name__} found {len(results)} items (insufficient). Retrying...")
                except Exception as e:
                    print(f"   ❌ Strategy Error: {e}")

            await browser.close()

    if not final_courses:
        print("❌ ALL STRATEGIES FAILED. No valid courses found.")
        return

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
