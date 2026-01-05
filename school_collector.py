import asyncio
import json
import os
import re
import argparse
from datetime import datetime

# --- NOTE: This function is only a fallback for Text Mode ---
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

async def fetch_course_data(url):
    """
    The "Tab Iterator" Scraper:
    1. Loads the main list.
    2. Harvests all Course Title Links.
    3. Opens each link in a NEW TAB, scrapes text, and closes it.
    """
    from playwright.async_api import async_playwright
    
    print(f"   🌍 Visiting: {url}")
    courses_found = []
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        # Create a "Context" (like a browser session) so cookies/login states are shared
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4) 

            # 1. HANDLE SEARCH (Kellogg/Booth often need this)
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Clicking Search to load list...")
                await search_btns.first.click()
                await page.wait_for_timeout(5000) 

            # 2. HARVEST LINKS
            # We look for links inside the table. 
            # Strategy: Find all <a> tags that are inside a table row (tr) or list item (li)
            print("   👀 Harvesting course links...")
            
            # This selector looks for links inside table cells (td a) OR list items (li a)
            # We filter out generic links like "View Description" or "Add to Cart"
            potential_links = await page.locator("tr td a, .course-list a, .result-item h3 a").all()
            
            valid_urls = []
            for link in potential_links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    
                    # Filter: Must be a real link, not a javascript:void(0)
                    if href and len(href) > 5 and "javascript" not in href:
                        # Filter: Text should look like a course code (e.g., "ACCT", "MKTG") or Title
                        if len(text) > 3 and "View Description" not in text:
                            
                            # Fix Relative URLs
                            if not href.startswith("http"):
                                base = "/".join(url.split("/")[:3]) # https://site.com
                                if href.startswith("/"):
                                    href = base + href
                                else:
                                    # Fallback for complex relative paths
                                    current_path = "/".join(url.split("/")[:-1])
                                    href = current_path + "/" + href
                            
                            valid_urls.append(href)
                except: pass
            
            # Deduplicate
            valid_urls = list(set(valid_urls))
            print(f"   ✅ Found {len(valid_urls)} unique course links.")
            
            if len(valid_urls) == 0:
                print("   ⚠️ No links found. The site might be using JavaScript buttons instead of <a> tags.")
                await browser.close()
                return []

            # 3. VISIT LOOP (Open New Tabs)
            # Limit to 60 for safety/speed, you can increase this.
            for i, link_url in enumerate(valid_urls[:500]):
                try:
                    # Open new page in same context
                    new_page = await context.new_page()
                    await new_page.goto(link_url, wait_until="domcontentloaded", timeout=15000)
                    
                    # Scrape
                    full_text = await new_page.inner_text("body")
                    
                    # Clean up the text to find the description
                    # We assume the whole page text is useful, but we try to find the "Title"
                    title = await new_page.title()
                    
                    # Save
                    courses_found.append({
                        "course": title.strip(),
                        "description": full_text[:2000] # Save first 2000 chars (usually contains description)
                    })
                    
                    print(f"      📄 [{i+1}] Scraped: {title[:30]}...")
                    
                    await new_page.close()
                    # Sleep to be polite to the server
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error on link {i}: {e}")
                    try: await new_page.close()
                    except: pass

            await browser.close()
            return courses_found

        except Exception as e:
            print(f"   ❌ Browser Error: {e}")
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

