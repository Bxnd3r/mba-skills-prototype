import asyncio
import json
import os
import re
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================================
# STRATEGY 1: CHICAGO BOOTH (Session Drill-Down)
# ==========================================
async def fetch_booth_data(context, url):
    print(f"   🏛️ Activated STRATEGY: Booth Drill-Down")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)

        # Find rows that look like "30000 - Financial Accounting"
        print("   👀 Identifying courses...")
        row_locator = page.locator("text=/^\\d{5}\\s-/")
        count = await row_locator.count()
        print(f"   ✅ Found {count} courses.")

        for i in range(min(count, 80)): # Safety limit
            try:
                # Re-locate elements after page refresh
                rows = page.locator("text=/^\\d{5}\\s-/")
                if await rows.count() <= i: break
                
                current_row = rows.nth(i)
                title_preview = await current_row.inner_text()
                
                # Click and Wait
                await current_row.click()
                await page.wait_for_selector("text=CONTENT", timeout=8000)
                
                # Scrape
                real_title = await page.locator("h1").inner_text()
                full_text = await page.inner_text("body")
                
                clean_desc = ""
                if "CONTENT" in full_text:
                    parts = full_text.split("CONTENT")
                    desc_chunk = parts[1]
                    # Cleanup footer garbage
                    if "PREREQUISITES" in desc_chunk: desc_chunk = desc_chunk.split("PREREQUISITES")[0]
                    elif "MATERIALS" in desc_chunk: desc_chunk = desc_chunk.split("MATERIALS")[0]
                    clean_desc = desc_chunk.strip()
                else:
                    clean_desc = full_text[:1000]

                if len(clean_desc) > 20:
                    print(f"      📄 [{i+1}] Captured: {real_title[:30]}...")
                    courses_found.append({"course": real_title, "description": clean_desc})

                # Go Back
                await page.go_back()
                await page.wait_for_selector("text=Course List", timeout=8000)
                await asyncio.sleep(0.5)

            except Exception:
                # If stuck, force reload list
                try: await page.goto(url, wait_until="domcontentloaded")
                except: pass

        await page.close()
        return courses_found
    except Exception as e:
        print(f"   ❌ Booth Error: {e}")
        return []

# ==========================================
# STRATEGY 2: IIT (Popup Bubble Clicker)
# ==========================================
async def fetch_iit_data(context, url):
    print(f"   🏛️ Activated STRATEGY: IIT Popup-Clicker")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(2)

        # IIT links are usually inside a table, e.g. <a href="..." onclick="...">MBA 501</a>
        # We look for links inside the course block container
        links = page.locator(".courseblock a, #programrequirementstextcontainer a")
        count = await links.count()
        print(f"   ✅ Found {count} potential course links.")

        for i in range(min(count, 100)):
            try:
                link = links.nth(i)
                code = await link.inner_text()
                
                # Filter: Only click things that look like course codes (e.g. "MBA 501")
                if not re.match(r"[A-Z]{2,4}\s\d{3}", code.strip()):
                    continue

                # Click to open popup
                await link.click()
                
                # Wait for popup to appear. IIT usually uses a div with class 'courseblock' in a modal
                # or a bubble that appears near the link. We wait for ANY text change or overlay.
                await asyncio.sleep(1) # Simple wait is safest for popups
                
                # Grab the popup content. 
                # Strategy: Look for the specific popup container OR just grab the visible text if it's an overlay
                # IIT usually loads content into a specific 'bubble' div
                popup_content = await page.locator(".courseblock, .bubble, .tooltip").last.inner_text()
                
                # Parse Title/Desc
                lines = [l.strip() for l in popup_content.split('\n') if l.strip()]
                if len(lines) >= 2:
                    title = lines[0] # "MBA 501 Financial Statement Applications"
                    desc = max(lines, key=len) # Longest line is description
                    
                    if len(desc) > 40:
                        print(f"      📄 Captured: {title[:30]}...")
                        courses_found.append({"course": title, "description": desc})

                # Close popup (Click 'Close' or just click body to dismiss)
                # Trying to click the "X" or body
                try:
                    close_btn = page.locator(".close-btn, .close")
                    if await close_btn.count() > 0:
                        await close_btn.first.click()
                    else:
                        await page.mouse.click(0, 0) # Click corner to dismiss
                except: pass
                
                await asyncio.sleep(0.5)

            except Exception:
                pass

        await page.close()
        return courses_found
    except Exception as e:
        print(f"   ❌ IIT Error: {e}")
        return []

# ==========================================
# STRATEGY 3: KELLOGG / STANDARD (Parallel Tabs)
# ==========================================
async def scrape_tab_parallel(context, url, sem):
    async with sem: # Limit 5 tabs at once
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # --- SMART TITLE FINDER ---
            real_title = "Unknown Course"
            # Explicitly ignore generic headers found on catalogs
            ignore_list = ["COURSE CATALOG", "COURSE DETAILS", "SCHEDULE", "SEARCH RESULTS", "CATALOG", "RETURN TO SEARCH"]
            
            headers = await page.locator("h1, h2, h3, .course-title, strong").all_inner_texts()
            for h in headers:
                clean_h = h.strip().upper()
                if len(clean_h) > 3 and len(clean_h) < 100:
                    if not any(ignored in clean_h for ignored in ignore_list):
                        real_title = h.strip()
                        break
            
            # Fallback to Tab Title
            if real_title == "Unknown Course":
                t = await page.title()
                real_title = t.split("-")[0].split("|")[0].strip()

            # --- SMART DESCRIPTION FINDER ---
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

            real_title = real_title.replace("\n", " ").strip()
            clean_desc = clean_desc.replace("\n", " ").strip()

            if len(clean_desc) > 20 and real_title != "Unknown Course":
                print(f"      ✅ Scraped: {real_title[:30]}...")
                return {"course": real_title, "description": clean_desc}
            return None
        except:
            try: await page.close()
            except: pass
            return None

async def fetch_parallel_data(context, url):
    print(f"   🚀 Activated STRATEGY: Parallel Tabs (Kellogg/Standard)")
    page = await context.new_page()
    courses_found = []
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # Search Clicker
        search_btns = page.locator("button:has-text('Search'), input[type='submit']")
        if await search_btns.count() > 0:
            print("   🖱️ Clicking Search...")
            await search_btns.first.click()
            await page.wait_for_timeout(5000)

        # Harvest Links
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
        print(f"   ✅ Found {len(valid_urls)} unique links.")

        # Execute Parallel
        sem = asyncio.Semaphore(5) 
        tasks = []
        for link_url in valid_urls[:100]: 
            tasks.append(scrape_tab_parallel(context, link_url, sem))
        
        results = await asyncio.gather(*tasks)
        courses_found = [r for r in results if r is not None]
        
        await page.close()
        return courses_found
    except Exception as e:
        print(f"   ❌ Browser Error: {e}")
        return []

# ==========================================
# MAIN ROUTER
# ==========================================
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["text", "url"], required=True)
    parser.add_argument("--input", help="URL", required=False)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    final_courses = []

    if args.mode == "text":
        print("ℹ️ Running in Text Mode (Manual Dump)")
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                # Basic parser for manual text
                text = f.read()
                lines = text.split('\n')
                for line in lines:
                    parts = re.split(r'(\t|\s{2,})', line.strip())
                    if len(parts) >= 3:
                        final_courses.append({"course": parts[0], "description": parts[2]})
        else:
            print("❌ Error: pending_audit.txt missing")
            return

    elif args.mode == "url":
        if not args.input:
            print("❌ Error: URL required")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # --- SMART ROUTING ---
            u = args.input.lower()
            if "chicagobooth.edu" in u:
                final_courses = await fetch_booth_data(context, args.input)
            elif "iit.edu" in u:
                final_courses = await fetch_iit_data(context, args.input)
            else:
                # Default for Kellogg and others
                final_courses = await fetch_parallel_data(context, args.input)
            
            await browser.close()

    if not final_courses:
        print("❌ No courses captured.")
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
    print(f"✅ SUCCESS: Saved {len(final_courses)} courses to {filename}")

if __name__ == "__main__":
    asyncio.run(main())



