import asyncio
import json
import os
import re
import argparse
from datetime import datetime

def parse_raw_text(text):
    """
    Standardizes messy text into a clean Course List.
    """
    parsed = []
    lines = text.split('\n')
    
    # 1. Visual Gap (Tab Separated)
    gap_lines = [line for line in lines if re.search(r'(\t|\s{2,})', line.strip())]
    if len(gap_lines) > 5:
        print("   🔍 Detected 'Visual Gap' format.")
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = re.split(r'(\t|\s{2,})', line, maxsplit=1)
            if len(parts) >= 3:
                title = parts[0].strip()
                desc = parts[2].strip()
                if len(desc) > 10: 
                    parsed.append({"course": title, "description": desc})
        if parsed: return parsed

    # 2. Course Code Check
    print("   🔍 Checking for Course Codes...")
    code_pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = code_pattern.split(text)
    if len(matches) > 5:
        print("   🔍 Detected 'Course Code' format.")
        for i in range(1, len(matches), 2):
            title = matches[i].strip()
            desc = matches[i+1].strip() if i+1 < len(matches) else ""
            if len(desc) > 20:
                parsed.append({"course": title, "description": desc})
        return parsed

    return []

async def fetch_url_text(url):
    """
    Advanced Scraper V2: Handles Search Buttons + Detail Page Crawling.
    """
    from playwright.async_api import async_playwright
    
    print(f"   🌍 Visiting: {url}")
    
    full_corpus_text = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a context so we can open multiple tabs if needed
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4) 

            # --- 1. HANDLE SEARCH/LOAD BUTTONS ---
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Found Search button. Clicking...")
                try:
                    await search_btns.first.click()
                    await asyncio.sleep(5)
                except: pass

            # --- 2. CHECK FOR EXPANDERS (The easy case) ---
            expand_buttons = page.locator("text=View Description, text=More Info, .expand-icon")
            if await expand_buttons.count() > 0:
                print(f"   🖱️ Found expanders. Clicking...")
                count = await expand_buttons.count()
                for i in range(min(count, 50)): # Limit to 50 for speed
                    try: await expand_buttons.nth(i).click()
                    except: pass
                await asyncio.sleep(2)

            # --- 3. MASTER-DETAIL STRATEGY (The Chicago Booth Fix) ---
            # If the page text is short, assume the content is hidden in links.
            page_text = await page.inner_text("body")
            
            if len(page_text) < 5000: # Heuristic: Page is too empty, must be a link list
                print("   ⚠️ Page content is sparse. Activating 'Deep Crawler' for course links...")
                
                # Find all links inside table cells or list items
                # We specifically look for links that might be courses
                links = await page.locator("td a, .course-list a, .result-list a, div.course-title a").all()
                
                # Extract hrefs (URLs) so we don't have to click-and-back
                urls_to_visit = []
                for link in links:
                    try:
                        href = await link.get_attribute("href")
                        if href and len(href) > 5 and "javascript" not in href:
                            # Construct full URL if relative
                            if not href.startswith("http"):
                                # Basic join (can be improved with urljoin)
                                base = "/".join(url.split("/")[:3]) 
                                if href.startswith("/"):
                                    href = base + href
                                else:
                                    href = base + "/PublicApps/CourseSearch/" + href # Heuristic for Booth
                            urls_to_visit.append(href)
                    except: pass

                # Deduplicate
                urls_to_visit = list(set(urls_to_visit))
                print(f"   🔍 Found {len(urls_to_visit)} potential course links. Visiting top 30...")

                # VISIT THE LINKS (Limit to 30-50 to prevent timeouts)
                for i, link_url in enumerate(urls_to_visit[:200]):
                    try:
                        # Open a new tab (page) for each course to keep the main list safe
                        new_page = await context.new_page()
                        await new_page.goto(link_url, wait_until="domcontentloaded", timeout=15000)
                        
                        # Grab the text
                        course_text = await new_page.evaluate("document.body.innerText")
                        full_corpus_text += f"\n\n--- COURSE {i} ---\n{course_text}"
                        
                        await new_page.close()
                        print(f"      📄 Scraped link {i+1}")
                        await asyncio.sleep(0.5) 
                    except Exception as e:
                        print(f"      ❌ Error visiting link: {e}")
                        try: await new_page.close()
                        except: pass

            else:
                # If page was full of text, just grab it
                full_corpus_text = page_text

            await browser.close()
            return full_corpus_text

        except Exception as e:
            print(f"   ❌ Browser Error: {e}")
            await browser.close()
            return full_corpus_text

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["text", "url"], required=True)
    parser.add_argument("--input", help="URL or leave blank for pending_audit.txt")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    raw_text = ""
    
    if args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                raw_text = f.read()
            with open("pending_audit.txt", "w") as f: f.write("")
        else:
            print("❌ Error: pending_audit.txt is missing.")
            return

    elif args.mode == "url":
        if not args.input:
            print("❌ Error: --input URL is required for url mode.")
            return
        raw_text = await fetch_url_text(args.input)

    if not raw_text:
        print("❌ No text captured.")
        return

    print(f"   Processing {len(raw_text)} chars of text...")
    courses = parse_raw_text(raw_text)

    # Fallback if parsing fails but we scraped a lot of text (common with Deep Crawl)
    if not courses and len(raw_text) > 1000:
        print("⚠️ Warning: Standard regex failed, but we captured text.")
        print("   Saving raw dump for later analysis.")
        courses = [{"course": "Raw Dump", "description": raw_text}]

    os.makedirs("raw_school_data", exist_ok=True)
    safe_name = args.name.lower().replace(' ', '_')
    filename = f"raw_school_data/{safe_name}_curriculum.json"
    
    final_data = {
        "school": args.name,
        "source_url": args.input if args.mode == "url" else "manual_text",
        "date_collected": datetime.now().strftime("%Y-%m-%d"),
        "course_count": len(courses),
        "curriculum": courses
    }

    with open(filename, "w") as f: json.dump(final_data, f, indent=2)
    print(f"✅ SUCCESS: Saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
