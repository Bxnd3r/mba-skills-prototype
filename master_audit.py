import asyncio
import json
import os
import re
import time
import argparse
import google.generativeai as genai

# --- SETUP ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key: 
    genai.configure(api_key=api_key)

# FIX 1: Updated Model Name (gemini-pro is deprecated)
model = genai.GenerativeModel('gemini-2.5-flash')

def parse_text_dump(text):
    """
    Smart Parser V4:
    Handles Tabs (\t) AND Spaces.
    """
    parsed = []
    lines = text.split('\n')
    
    # --- CHECK 1: VISUAL GAP (Tabs or 2+ Spaces) ---
    # We look for lines that have a tab OR 2+ spaces in the middle
    gap_lines = [line for line in lines if re.search(r'(\t|\s{2,})', line.strip())]
    
    # If we find valid lines, use this method
    if len(gap_lines) > 5:
        print("DEBUG: Detected Visual Gap format (Tabs or Spaces).")
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Split by Tab OR 2+ Spaces
            parts = re.split(r'(\t|\s{2,})', line, maxsplit=1)
            
            # re.split keeps the delimiter, so we need to handle that
            # Result usually looks like: ['Title', '   ', 'Description']
            if len(parts) >= 3:
                title = parts[0].strip()
                desc = parts[2].strip() # Skip index 1 (the separator)
                
                if len(desc) > 10: 
                    parsed.append({"course": title, "text": desc})
        return parsed

    # --- CHECK 2: CODE PATTERN (Fallback) ---
    print("DEBUG: No gaps found. Checking for Course Codes.")
    code_pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = code_pattern.split(text)
    
    if len(matches) > 5:
        print("DEBUG: Detected Course Codes format.")
        for i in range(1, len(matches), 2):
            title = matches[i].strip()
            desc = matches[i+1].strip() if i+1 < len(matches) else ""
            if len(desc) > 20:
                parsed.append({"course": title, "text": desc})
        return parsed

    print("❌ Error: Could not determine file format.")
    return []

async def scrape_browser(url):
    from playwright.async_api import async_playwright
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
        print("❌ No courses found. (Check file format)")
        return

    # --- GEMINI AUDIT ---
    print(f"🧠 Auditing {len(results)} courses...")
    audited = []
    
    for item in results[:50]:
        try:
            prompt = f"Analyze course: {item['course']}\nText: {item['text'][:1500]}\nScore 1-5 on Digital, Quant, Strategy, Management, Communication, Regulation. Return ONLY JSON."
            res = model.generate_content(prompt)
            
            clean = res.text.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
                
            skills = json.loads(clean)
            audited.append({"course": item['course'], "skills": skills, "text": item['text'][:300]})
            print(f"   OK: {item['course'][:30]}...")
            time.sleep(1) # Rate limit safety
        except Exception as e:
            print(f"   FAIL: {item['course'][:30]}... Error: {e}")
            continue

    school_id = args.name.lower().replace(" ", "_")
    filename = f"{school_id}_audit.json"
    
    if audited:
        with open(filename, "w") as f: json.dump(audited, f, indent=2)
        print(f"✅ Created {filename}")
    else:
        print("❌ Audit finished but produced 0 results.")

if __name__ == "__main__":
    asyncio.run(main())






