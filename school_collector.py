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
    Kellogg-Optimized Scraper: Search -> Expand All -> Scrape.
    """
    from playwright.async_api import async_playwright
    
    print(f"   🌍 Visiting: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4) 

            # --- 1. HANDLE SEARCH BUTTON (Required for Kellogg) ---
            # We look for the "Search" button to load the initial list
            search_btns = page.locator("button:has-text('Search'), input[type='submit'], a.btn-search")
            if await search_btns.count() > 0:
                print("   🖱️ Found Search button. Clicking to load courses...")
                try:
                    await search_btns.first.click()
                    # Wait for the spinner to go away / table to load
                    await asyncio.sleep(6) 
                    await page.wait_for_load_state("networkidle") 
                except: pass

            # --- 2. THE "EXPANDER" STRATEGY ---
            # Instead of opening links, we click "View Description"
            
            # Find all potential expanders
            # Kellogg uses "View Description", others use "More" or arrow icons
            expanders = page.locator("text=View Description, text=More Info, a[id*='Description']")
            count = await expanders.count()

            if count > 0:
                print(f"   🖱️ Found {count} 'View Description' toggles.")
                print("      Clicking them one by one to reveal text (this ensures we capture it)...")
                
                # We loop through them. Limit to 150 to prevent timeouts.
                # If there are 400 courses, we'll get the top 150 which is plenty for analysis.
                for i in range(min(count, 150)):
                    try:
                        # We re-query the element to avoid "Stale Element" errors
                        btn = expanders.nth(i)
                        if await btn.is_visible():
                            await btn.click()
                            # Tiny sleep to let the text render
                            if i % 10 == 0: await asyncio.sleep(0.5) 
                    except Exception as e:
                        # Sometimes one click fails, just keep going
                        pass
                
                print("      ✅ Finished expanding. Waiting for text to settle...")
                await asyncio.sleep(3)

            # --- 3. SCRAPE THE FULL PAGE ---
            # Now that everything is expanded, we grab the Body Text
            full_text = await page.inner_text("body")
            
            print(f"   📏 Captured {len(full_text)} chars of text.")
            
            await browser.close()
            return full_text

        except Exception as e:
            print(f"   ❌ Browser Error: {e}")
            await browser.close()
            return ""

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

    # Fallback: If Regex fails but we have text, save the raw dump
    if not courses and len(raw_text) > 5000:
        print("⚠️ Warning: Auto-parser couldn't split courses perfectly.")
        print("   Saving raw text dump for AI Analysis later.")
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
