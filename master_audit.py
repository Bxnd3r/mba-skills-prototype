import asyncio
import json
import os
import re
import time
import sys
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- SETUP ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

async def run_audit(input_data, school_name):
    print(f"🕵️ Auditing: {school_name}...")
    results = []

    # CHECK: Is the input a URL or raw text?
    if input_data.startswith("http"):
        results = await scrape_url(input_data)
    else:
        print("📝 Raw text detected. Bypassing browser and parsing locally...")
        results = parse_raw_text(input_data)

    if not results:
        print("❌ No courses found to audit.")
        ensure_registry_exists()
        return

    # --- GEMINI-PRO AUDIT ---
    print(f"🧠 Auditing {len(results)} courses with gemini-pro...")
    audited = []
    for item in results[:50]: # Safety limit
        try:
            prompt = f"Analyze course: {item['course']}\nText: {item['text'][:2000]}\nScore 1-5 on Digital, Quant, Strategy, Management, Communication, Regulation. Return ONLY JSON."
            res = model.generate_content(prompt)
            clean = res.text.strip().replace("```json","").replace("```","")
            audited.append({"course": item['course'], "skills": json.loads(clean), "text": item['text'][:300]})
            time.sleep(1)
        except: continue

    # SAVE
    school_id = school_name.lower().replace(" ", "_")
    filename = f"{school_id}_audit.json"
    with open(filename, "w") as f: json.dump(audited, f, indent=2)
    update_registry(school_id, school_name, filename)
    print(f"✅ SUCCESS! Created {filename}")

def parse_raw_text(text):
    """Splits pasted text into course chunks based on course code patterns."""
    # Look for patterns like 'MGMT-GB.2314' or 'ACCT-3000'
    pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = pattern.split(text)
    
    parsed = []
    # Every match is followed by its description text in the split list
    for i in range(1, len(matches), 2):
        title = matches[i].strip()
        description = matches[i+1].strip() if i+1 < len(matches) else ""
        if len(description) > 20:
            parsed.append({"course": title, "text": description})
    return parsed

async def scrape_url(url):
    """Existing logic for Booth, Kellogg, etc."""
    # ... (Keep the Reset-Loop logic here as a fallback)
    return [] 

def ensure_registry_exists():
    if not os.path.exists("registry.json"):
        with open("registry.json", "w") as f: json.dump([], f)

def update_registry(school_id, name, filename):
    ensure_registry_exists()
    with open("registry.json", "r") as f: reg = json.load(f)
    reg = [r for r in reg if r['id'] != school_id]
    reg.append({"id": school_id, "name": name, "audit": filename, "color": "rgba(0,0,0,0.5)"})
    with open("registry.json", "w") as f: json.dump(reg, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_audit(sys.argv[1], sys.argv[2]))
