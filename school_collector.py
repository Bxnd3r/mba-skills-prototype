import asyncio
import json
import os
import re
import argparse
from datetime import datetime

def parse_raw_text(text):
    # Fallback for text mode
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

# --- WORKER FUNCTION (Scrapes one single tab) ---
async def scrape_single_course(context, url, sem):
    async with sem: # Wait for a free "slot" (limit 5 tabs at once)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # A. GET REAL TITLE (H1)
            real_title = "Unknown Course"
            try:
                h1 = page.locator("h1")
                if await h1.count() > 0:
                    real_title = await h1.first.text_content()
                else:
                    real_title = await page.locator("h2").first.text_content()
            except: pass

            # B. GET CLEAN DESCRIPTION
            full_text = await page.inner_text("body")
            clean_desc = ""
            
            if "DESCRIPTION" in full_text:
                parts = full_text.split("DESCRIPTION")
                if len(parts) > 1:
                    clean_desc = parts[1].strip()[:1500]
            elif "Overview" in full_text:
                parts = full_text.split("Overview")
                if len(parts) > 1:
                    clean_desc = parts[1].strip()[:1500]
            else:
                clean_desc = full_text[:1500]

            # Cleanup
            real_title = real_title.strip().replace("\n", " ")
            await page.close()

            if len(clean_desc) > 20:
                print(f"      ✅ Scraped: {real_title[:30]}...")
                return {"course": real_title, "description": clean_desc}
            else:
                return None

        except Exception:
            # Silently fail on bad links to keep speed up
            try: await page.close()
            except: pass
            return None

async def fetch_course_data(url):
    """
    Turbo Scraper: Harvests links, then opens 5 tabs at once.
    """
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

            # 1. CLICK SEARCH (If needed)
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Clicking Search...")
                await search_btns.first.click()
                await page.wait_for_timeout(5000) 

            # 2. HARVEST LINKS
            print("   👀 Harvesting links...")
            potential_links = await page.locator("tr td a, .course-list a, .result-item h3 a").all()
            
            valid_urls = []
            for link in potential_links:
                try:
                    href = await link.get_attribute("href")
                    if href and len(href) > 5 and "javascript" not in href:
                        if not href.startswith("http"):
                            base = "/".join(url.split("/")[:3]) 
                            if href.startswith("/"):
                                href = base + href
                            else:
                                current_path = "/".join(url.split("/")[:-1])
                                href = current_path + "/" + href
                        valid_urls.append(href)
                except: pass
            
            valid_urls = list(set(valid_urls))
            print(f"   ✅ Found {len(valid_urls)} unique links. Starting Turbo Scrape (5x speed)...")
            
            # 3. PARALLEL EXECUTION
            # This 'Semaphore' ensures we never open more than 5 tabs at once
            sem = asyncio.Semaphore(5) 
            tasks = []
            
            # Limit to 80 courses to prevent timeouts, but do them in parallel
            for link_url in valid_urls[:80]:
                tasks.append(scrape_single_course(context, link_url, sem))
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # Filter out failures (None)
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
        final_courses = await fetch_course_data(args.input)

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
