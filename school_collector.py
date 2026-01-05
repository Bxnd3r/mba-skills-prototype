import asyncio
import json
import os
import re
import argparse
from datetime import datetime

# --- NOTE: This function is now only a fallback for Text Mode ---
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
    The "Iterator" Scraper:
    1. Finds the rows.
    2. Clicks 'View Description' for a row.
    3. Scrapes that specific row immediately.
    4. Moves to the next.
    Returns: A structured LIST of dicts (bypassing regex parsing).
    """
    from playwright.async_api import async_playwright
    
    print(f"   🌍 Visiting: {url}")
    courses_found = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4) 

            # 1. HANDLE SEARCH
            search_btns = page.locator("button:has-text('Search'), input[type='submit']")
            if await search_btns.count() > 0:
                print("   🖱️ Clicking Search...")
                await search_btns.first.click()
                await page.wait_for_timeout(5000) # Wait for table

            # 2. IDENTIFY ROWS via "View Description" buttons
            # Each button lives inside a course row. We use the button as our anchor.
            expanders = page.locator("text=View Description")
            count = await expanders.count()
            
            if count == 0:
                print("   ⚠️ No 'View Description' buttons found. Trying generic 'tr' rows...")
                # Fallback logic could go here, but for Kellogg this is key.
            
            print(f"   found {count} courses. Scraping row-by-row (this ensures accuracy)...")
            
            # 3. ITERATE ROW-BY-ROW
            # We limit to 60 for testing speed, but you can increase this.
            for i in range(min(count, 80)): 
                try:
                    button = expanders.nth(i)
                    
                    # A. CLICK
                    if await button.is_visible():
                        await button.click(force=True)
                        await asyncio.sleep(0.5) # Wait for animation
                    
                    # B. IDENTIFY PARENT CONTAINER
                    # We go up 3-4 levels to find the 'tr' or main 'div' that holds both title and description
                    # This uses XPath '..' to go up to parent
                    row_handle = await button.locator("xpath=../../..").element_handle()
                    
                    # C. SCRAPE TEXT FROM THIS CONTAINER ONLY
                    row_text = await row_handle.inner_text()
                    
                    # D. CLEANUP
                    # Row text usually looks like: "ACCT 101 \n Intro to Accounting \n View Description \n This course covers..."
                    lines = [line.strip() for line in row_text.split('\n') if line.strip()]
                    
                    # Heuristic: 
                    # Title is usually line 0 or 1.
                    # Description is the longest line in the block.
                    title = lines[0] + " " + lines[1] if len(lines) > 1 else lines[0]
                    description = max(lines, key=len) # The longest chunk is likely the description
                    
                    if len(description) > 40 and "View Description" not in description:
                        courses_found.append({
                            "course": title[:50], # Keep title short
                            "description": description
                        })
                        print(f"      ✅ [{i+1}] Scraped: {title[:20]}...")
                    
                except Exception as e:
                    # print(f"Error on row {i}: {e}")
                    pass

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
    
    # --- URL MODE (Smart Iterator) ---
    if args.mode == "url":
        if not args.input:
            print("❌ Error: --input URL is required.")
            return
        # This now returns a LIST, not text
        final_courses = await fetch_course_data(args.input)

    # --- TEXT MODE (Legacy Fallback) ---
    elif args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                raw_text = f.read()
            with open("pending_audit.txt", "w") as f: f.write("")
            print(f"   Processing manual text...")
            final_courses = parse_raw_text(raw_text)
        else:
            print("❌ Error: pending_audit.txt is missing.")
            return

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
