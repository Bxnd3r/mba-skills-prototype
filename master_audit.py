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
    """
    Smart Parser:
    1. Tries to find strict course codes (e.g. BUS 101, CS-400).
    2. If none found, falls back to splitting by large gaps (3+ spaces).
    """
    parsed = []
    
    # --- STRATEGY 1: STRICT CODES ---
    # Looks for patterns like "BUS 101", "CS-405", "MKT.500"
    code_pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = code_pattern.split(text)
    
    # If we found more than 5 matches, assume this file uses Course Codes
    if len(matches) > 5:
        print("DEBUG: Detected Course Codes format.")
        for i in range(1, len(matches), 2):
            title = matches[i].strip()
            desc = matches[i+1].strip() if i+1 < len(matches) else ""
            if len(desc) > 20:
                parsed.append({"course": title, "text": desc})
        return parsed

    # --- STRATEGY 2: FALLBACK (SPACES) ---
    print("DEBUG: No codes found. Switching to visual-spacing format.")
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Split line where there are 3 or more spaces
        parts = re.split(r'\s{3,}', line, maxsplit=1)
        
        if len(parts) >= 2:
            title = parts[0].strip()
            desc = parts[1].strip()
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


