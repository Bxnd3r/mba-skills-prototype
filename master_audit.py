import json
import os
import re
import time
import asyncio
import google.generativeai as genai

# --- SETUP ---
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

async def run_audit(school_name):
    print(f"🕵️ Auditing: {school_name}...")
    
    # 1. Check for the local text file first to bypass GitHub input limits
    if os.path.exists("pending_audit.txt"):
        print("📖 Found pending_audit.txt. Processing large payload...")
        with open("pending_audit.txt", "r", encoding="utf-8") as f:
            input_data = f.read()
        results = parse_raw_text(input_data)
        # Optional: Delete or clear the file after reading so it doesn't re-run
    else:
        print("❌ Error: No pending_audit.txt found. Please upload your text dump first.")
        return

    if not results:
        print("❌ No courses identified in the text.")
        return

    # --- GEMINI-PRO AUDIT ---
    print(f"🧠 Auditing {len(results)} courses with gemini-pro...")
    audited = []
    for item in results[:60]: # Increased limit for NYU
        try:
            prompt = f"Analyze course: {item['course']}\nText: {item['text'][:1500]}\nScore 1-5 on Digital, Quant, Strategy, Management, Communication, Regulation. Return ONLY JSON."
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
    # ... after the update_registry(school_id, school_name, filename) line ...
    
    if os.path.exists("pending_audit.txt"):
        with open("pending_audit.txt", "w") as f:
            f.write("") # This wipes the file content but keeps the file exists
        print("🧹 pending_audit.txt has been cleared for the next run.")
    print(f"✅ SUCCESS! Created {filename}")
    

def parse_raw_text(text):
    # Regex to find NYU-style codes (e.g., MGMT-GB.2314)
    pattern = re.compile(r"([A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}.+)")
    matches = pattern.split(text)
    parsed = []
    for i in range(1, len(matches), 2):
        title = matches[i].strip()
        description = matches[i+1].strip() if i+1 < len(matches) else ""
        if len(description) > 20:
            parsed.append({"course": title, "text": description})
    return parsed

def update_registry(school_id, name, filename):
    reg_path = "registry.json"
    reg = []
    if os.path.exists(reg_path):
        with open(reg_path, "r") as f: reg = json.load(f)
    reg = [r for r in reg if r['id'] != school_id]
    reg.append({"id": school_id, "name": name, "audit": filename, "color": "rgba(0,0,0,0.5)"})
    with open(reg_path, "w") as f: json.dump(reg, f, indent=2)

if __name__ == "__main__":
    import sys
    # Only needs the name now since data is in the file
    asyncio.run(run_audit(sys.argv[1]))
