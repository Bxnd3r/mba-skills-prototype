import asyncio
import json
import os
import re
import argparse
from datetime import datetime

# --- HELPER: TEXT PARSER ---
def parse_raw_text(text):
    parsed = []
    lines = text.split('\n')
    gap_lines = [line for line in lines if re.search(r'(\t|\s{2,})', line.strip())]
    if len(gap_lines) > 5:
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = re.split(r'(\t|\s{2,})', line, maxsplit=1)
            if len(parts) >= 3:
                title = parts[0].strip()
                desc = parts[2].strip()
                if len(desc) > 25: 
                    parsed.append({"course": title, "description": desc})
        return parsed
    return []

# --- SPECIAL MODE: CHICAGO BOOTH ---
async def fetch_booth_data(url):
    """
    Drill-Down Strategy for Booth:
    1. Click Row.
    2. Wait for 'CONTENT' header.
    3. Scrape.
    4. Go Back.
    5. Repeat.
    """
    from playwright.async_api import async_playwright
    print(f"   🏛️ Activated BOOTH MODE for: {url}")
    
    courses_found = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a context to maintain session state
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)

            # 1. FIND ROWS
            # We look for the text pattern "30000 - " (5 digits + dash)
            # This targets the clickable labels in the list
            print("   👀 Identifying courses...")
            # We use a Regex locator to find lines starting with 5 digits
            row_locator = page.locator("text=/^\\d{5}\\s-/")
            count = await row_locator.count()
            print(f"   ✅ Found {count} courses.")

            # 2. DRILL DOWN LOOP
            # We have to go one-by-one. Limit to 50 for safety.
            for i in range(min(count, 50)):
                try:
                    # We MUST re-locate the element every loop because the page refreshes
                    rows = page.locator("text=/^\\d{5}\\s-/")
                    if await rows.count() <= i: break
                    
                    current_row = rows.nth(i)
                    title_preview = await current_row.inner_text()
                    
                    print(f"      👉 [{i+1}] Clicking: {title_preview.strip()}...")
                    
                    # CLICK
                    await current_row.click()
                    
                    # WAIT FOR DETAIL
                    # We wait for the "CONTENT" header which is unique to the detail page
                    await page.wait_for_selector("text=CONTENT", timeout=8000)
                    
                    # SCRAPE
                    real_title = await page.locator("h1").inner_text() # "FINANCIAL ACCOUNTING (30000)"
                    
                    # Description is text below "CONTENT"
                    # We grab the whole body and split it
                    full_text = await page.inner_text("body")
                    clean_desc = ""
                    
                    if "CONTENT" in full_text:
                        # Split by "CONTENT" and take the part after
                        parts = full_text.split("CONTENT")
                        # Further split by "PREREQUISITES" or "MATERIALS" to clean up footer
                        desc_chunk = parts[1]
                        if "PREREQUISITES" in desc_chunk:
                            desc_chunk = desc_chunk.split("PREREQUISITES")[0]
                        elif "MATERIALS" in desc_chunk:
                            desc_chunk = desc_chunk.split("MATERIALS")[0]
                        clean_desc = desc_chunk.strip()
                    else:
                        clean_desc = full_text[:1000] # Fallback

                    # SAVE
                    if len(clean_desc) > 20:
                        courses_found.append({"course": real_title, "description": clean_desc})
                        print(f"         📄 Captured: {len(clean_desc)} chars")

                    # GO BACK
                    # Try browser back first
                    await page.go_back()
                    
                    # Wait for the list to reappear
                    await page.wait_for_selector("text=Course List", timeout=8000)
                    await asyncio.sleep(1) # Tiny pause to let list re-render

                except Exception as e:
                    print(f"      ❌ Error on row {i}: {e}")
                    # If we get stuck, try to force go back to list
                    try: await page.goto(url, wait_until="domcontentloaded")
                    except: pass

            await browser.close()
            return courses_found

        except Exception as e:
            print(f"   ❌ Browser Error: {e}")
            await browser.close()
            return []

# --- STANDARD TURBO MODE (For other schools) ---
async def scrape_single_course(context, url, sem):
    async with sem: 
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            real_title = "Unknown Course"
            # Smart Title Finder
            headers = await page.locator("h1, h2, h3, .course-title, strong").all_inner_texts()
            ignore_list = ["COURSE CATALOG", "COURSE DETAILS", "SCHEDULE", "SEARCH RESULTS", "CATALOG"]
            for h in headers:
                clean_h = h.strip().upper()
                if len(clean_h) > 3 and len(clean_h) < 100:
                    if not any(ignored in clean_h for ignored in ignore_list):
                        real_title = h.strip()
                        break
            
            if real_title == "Unknown Course":
                t = await page.title()
                real_title = t.split("-")[0].split("|")[0].strip()

            full_text = await page.inner_text("body")
            clean_desc = ""
            if "DESCRIPTION" in full_text:
                parts = full_text.split("DESCRIPTION")
                if len(parts) > 1: clean_desc = parts[1].strip()[:1500]
            elif "Overview" in full_text:
                parts = full_text.split("Overview")
                if len(parts) > 1: clean_desc = parts[1].strip()[:1500]
            else:
                clean_desc = full_text[:1500]

            await page.close()
            if len(clean_desc) > 20 and real_title != "Unknown Course":
                print(f"      ✅ Scraped: {real_title[:30]}...")
                return {"course": real_title, "description": clean_desc}
            return None
        except:
            try: await page.close()
            except: pass
            return None

async def fetch_turbo_data(url):
    from playwright.async_api import async_playwright
    print(f"   🌍 Visiting Main Catalog: {url}")
    courses_found = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3) 

            # Search Clicker
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Clicking Search...")
                await search_btns.first.click()
                await page.wait_for_timeout(5000) 

            print("   👀 Harvesting links...")
            potential_links = await page.locator("tr td a, .course-list a, .result-item h3 a").all()
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
            print(f"   ✅ Found {len(valid_urls)} unique links. Starting Turbo Scrape (5x speed)...")
            
            sem = asyncio.Semaphore(5) 
            tasks = []
            for link_url in valid_urls[:100]: # Limit 100
                tasks.append(scrape_single_course(context, link_url, sem))
            
            results = await asyncio.gather(*tasks)
            courses_found = [r for r in results if r is not None]
            await browser.close()
            return courses_found
        except Exception as e:
            print(f"   ❌ Main Browser Error: {e}")
            await browser.close()
            return []

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["text", "url"], required=True)
    parser.add_argument("--input", help="URL or leave blank for pending_audit.txt")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    final_courses = []
    
    if args.mode == "url":
        if not args.input:
            print("❌ Error: --input URL is required.")
            return
        
        # --- ROUTER LOGIC ---
        # Detect if this is Chicago Booth and use the Special Mode
        if "chicagobooth" in args.input.lower():
            final_courses = await fetch_booth_data(args.input)
        else:
            final_courses = await fetch_turbo_data(args.input)

    elif args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                raw_text = f.read()
            with open("pending_audit.txt", "w") as f: f.write("")
            final_courses = parse_raw_text(raw_text)
        else:
            print("❌ Error: pending_audit.txt is missing.")
            return

    if not final_courses:
        print("❌ No courses captured.")
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
    print(f"✅ SUCCESS: Saved {len(final_courses)} courses to {filename}")

if __name__ == "__main__":
    asyncio.run(main())


