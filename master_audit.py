import asyncio
import json
import os
import re
import argparse
from datetime import datetime
from playwright.async_api import async_playwright # Needed for URL mode

def parse_raw_text(text):
    """
    Standardizes messy text into a clean Course List using Regex.
    """
    parsed = []
    lines = text.split('\n')
    
    # 1. Visual Gap Check (Tab/Space Separated)
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

    # 2. Course Code Check (e.g., "MKTG 101")
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
    Uses Playwright to render the page and grab visible text.
    """
    print(f"   🌍 Visiting: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Wait a bit for dynamic content (React/Angular sites)
            await asyncio.sleep(3)
            
            # Smart Scrape: Try to get main content, fall back to body
            content = await page.evaluate("""() => {
                // Try to find a main curriculum container
                const main = document.querySelector('main') || document.querySelector('.course-list') || document.body;
                return main.innerText;
            }""")
            await browser.close()
            return content
        except Exception as e:
            print(f"   ❌ Network Error: {e}")
            await browser.close()
            return ""

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["text", "url"], required=True)
    parser.add_argument("--input", help="URL or leave blank for pending_audit.txt")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    raw_text = ""
    
    # --- PHASE 1: GET TEXT ---
    if args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                raw_text = f.read()
            # Clear file
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

    # --- PHASE 2: PARSE ---
    print(f"   Processing {len(raw_text)} chars of text...")
    courses = parse_raw_text(raw_text)

    if not courses:
        print("⚠️ Warning: Auto-parser couldn't find clear course/description pairs.")
        print("   Saving raw dump anyway for manual review.")
        # We save a "fallback" object so we don't lose the data
        courses = [{"course": "Raw Dump", "description": raw_text[:50000]}]

    # --- PHASE 3: SAVE ---
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
