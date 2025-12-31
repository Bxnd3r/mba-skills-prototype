import asyncio
import json
import os
import re
import time
import argparse
import google.generativeai as genai
# REMOVED: from playwright.async_api import async_playwright

# --- SETUP ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key: genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def parse_text_dump(text):
    """Parses text where lines follow: Title   Description"""
    parsed = []
    # Split the massive text blob into individual lines
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue  # Skip empty lines
        
        # Split by 3 spaces (or more)
        parts = re.split(r'\s{3,}', line, maxsplit=1)
        
        if len(parts) >= 2:
            title = parts[0].strip()
            desc = parts[1].strip()
            # Only save if description looks real
            if len(desc) > 10:
                parsed.append({"course": title, "text": desc})
                
    return parsed

async def scrape_browser(url):
    """The 'Reset-Loop' strategy for complex URLs."""
    # MOVE IMPORT HERE:
    from playwright.async_api import async_playwright
    
    # (Existing Reset-Loop logic goes here)
    print(f"🌍 Starting browser scrape for {url}...")
    return []

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["url", "text"], required=True)
    parser.add_argument("--input", help="URL or raw text")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    results = []
    
    if args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                data = f.read()
            results = parse_text_dump(data)
            # Clear file
            with open("pending_audit.txt", "w") as f: f.write("")
        else:
            print("❌ Error: pending_audit.txt is empty or missing.")
            return
    else:
        results = await scrape_browser(args.input)

    if not results:
        print("❌ No courses found.")
        return

    # --- GEMINI-PRO AUDIT ---
    print(f"🧠 Auditing {len(results)} courses...")
    audited = []
    for item in results[:50]:
        try:
            prompt = f"Analyze course: {item['course']}\nText: {item['text'][:1500]}\nScore 1-5 on Digital, Quant, Strategy, Management, Communication, Regulation. Return ONLY JSON."
            res = model.generate_content(prompt)
            clean = res.text.strip().replace("```json","").replace("```","")
            audited.append({"course": item['course'], "skills": json.loads(clean), "text": item['text'][:300]})
            time.sleep(1)
        except: continue

    school_id = args.name.lower().replace(" ", "_")
    filename = f"{school_id}_audit.json"
    with open(filename, "w") as f: json.dump(audited, f, indent=2)
    
    # Update Registry logic here...
    print(f"✅ Created {filename}")

if __name__ == "__main__":
    asyncio.run(main())

