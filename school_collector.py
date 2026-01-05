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
    
    # 1. Visual Gap
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
                # Only save if description looks real (longer than a generic word)
                if len(desc) > 25: 
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
            if len(desc) > 25:
                parsed.append({"course": title, "description": desc})
        return parsed

    return []

async def fetch_url_text(url):
    """
    Advanced Scraper V3: Aggressive Deep Crawling.
    """
    from playwright.async_api import async_playwright
    
    print(f"   🌍 Visiting: {url}")
    
    full_corpus_text = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4) 

            # --- 1. HANDLE SEARCH BUTTONS ---
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Found Search button. Clicking...")
                try:
                    await search_btns.first.click()
                    await asyncio.sleep(6) # Give it time to load the table
                except: pass

            # --- 2. CHECK FOR EXPANDERS ---
            expanders_clicked = 0
            expand_buttons = page.locator("text=View Description, text=More Info, .expand-icon, .kellogg-expand")
            if await expand_buttons.count() > 0:
                print(f"   🖱️ Found expanders. Clicking...")
                count = await expand_buttons.count()
                for i in range(min(count, 100)): 
                    try: 
                        await expand_buttons.nth(i).click()
                        expanders_clicked += 1
                    except: pass
                await asyncio.sleep(2)

            # --- 3. DECISION TIME: DO WE HAVE DATA? ---
            page_text = await page.inner_text("body")
            print(f"   📏 Current Page Text Length: {len(page_text)} chars")
            
            # AGGRESSIVE CHECK: If text is < 100k OR we didn't click expanders, we assume we missed the details.
            if len(page_text) < 100000 and expanders_clicked == 0:
                print("   ⚠️ Text is too short (Descriptions likely hidden). Activating 'Deep Crawler'...")
                
                # Targeted Selectors for Course Links (Kellogg, Booth, etc.)
                # We look for links inside tables or lists
                possible_links = await page.locator("td a, .course-list a, .result-list a, h3 a, h4 a").all()
                
                urls_to_visit = []
                for link in possible_links:
                    try:
                        href = await link.get_attribute("href")
                        # Filter out garbage links
                        if href and len(href) > 5 and "javascript" not in href and "mailto" not in href:
                            # Filter out nav links (Home, About, etc)
                            if any(x in href.lower() for x in ["login", "privacy", "contact", "home"]): continue
                            
                            # Fix Relative URLs
                            if not href.startswith("http"):
                                base = "/".join(url.split("/")[:3]) # https://site.com
                                if href.startswith("/"):
                                    href = base + href
                                else:
                                    # Fallback for relative paths
                                    current_dir = "/".join(url.split("/")[:-1])
                                    href = current_dir + "/" + href
                            
                            urls_to_visit.append(href)
                    except: pass

                # Deduplicate
                urls_to_visit = list(set(urls_to_visit))
                print(f"   🔍 Found {len(urls_to_visit)} potential course links. Visiting top 60...")

                # VISIT LINKS (Limit 60 to prevent timeout)
                for i, link_url in enumerate(urls_to_visit[:60]):
                    try:
                        new_page = await context.new_page()
                        await new_page.goto(link_url, wait_until="domcontentloaded", timeout=10000)
                        
                        # Grab title and body
                        sub_text = await new_page.inner_text("body")
                        
                        # Only keep if it looks like a course page (has "Description" or "Credits")
                        if "Description" in sub_text or "Overview" in sub_text:
                            full_corpus_text += f"\n\n--- COURSE ENTRY {i} ---\n{sub_text}"
                            print(f"      📄 Scraped link {i+1}: {len(sub_text)} chars")
                        
                        await new_page.close()
                        await asyncio.sleep(0.5) 
                    except: 
                        try: await new_page.close()
                        except: pass
            else:
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

    # If Regex failed but we have data (Deep Crawl mode often produces text that regex misses)
    # We save the raw dump as a fallback so we don't lose the scrape
    if not courses and len(raw_text) > 1000:
        print("⚠️ Warning: Standard regex failed, but we captured text.")
        print("   Saving raw dump as 'Manual_Review' course.")
        courses = [{"course": "Raw Data Dump", "description": raw_text}]

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
