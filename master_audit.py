import asyncio
import json
import os
import re
import time
import argparse
import google.generativeai as genai
from playwright.async_api import async_playwright

# --- SETUP ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key: genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def parse_text_dump(text):
    """Parses raw text based on standard course patterns."""
    pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = pattern.split(text)
    parsed = []
    for i in range(1, len(matches), 2):
        title = matches[i].strip()
        desc = matches[i+1].strip() if i+1 < len(matches) else ""
        if len(desc) > 20:
            parsed.append({"course": title, "text": desc})
    return parsed

async def scrape_browser(url):
    """The 'Reset-Loop' strategy for complex URLs."""
    # (Placeholder for the Strategy C logic we refined for Booth/Kellogg)
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
            # Clear the file after reading
            with open("pending_audit.txt", "w") as f: f.write("")
        else:
            print("❌ Error: pending_audit.txt is missing.")
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

    # SAVE & REGISTER
    school_id = args.name.lower().replace(" ", "_")
    filename = f"{school_id}_audit.json"
    with open(filename, "w") as f: json.dump(audited, f, indent=2)
    
    update_registry(school_id, args.name, filename)
    print(f"✅ Created {filename}")

def update_registry(school_id, name, filename):
    reg_path = "registry.json"
    reg = []
    if os.path.exists(reg_path):
        with open(reg_path, "r") as f: reg = json.load(f)
    reg = [r for r in reg if r['id'] != school_id]
    reg.append({"id": school_id, "name": name, "audit": filename, "color": "rgba(0,0,0,0.5)"})
    with open(reg_path, "w") as f: json.dump(reg, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
