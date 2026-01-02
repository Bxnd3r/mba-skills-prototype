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

# Use the 2.5 model (or 1.5-flash if 2.5 hits limits)
model = genai.GenerativeModel('gemini-2.5-flash')

def parse_text_dump(text):
    """
    Smart Parser V4: Handles Tabs/Spaces or Course Codes.
    """
    parsed = []
    lines = text.split('\n')
    
    # 1. Visual Gap Check
    gap_lines = [line for line in lines if re.search(r'(\t|\s{2,})', line.strip())]
    if len(gap_lines) > 5:
        print("DEBUG: Detected Visual Gap format.")
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = re.split(r'(\t|\s{2,})', line, maxsplit=1)
            if len(parts) >= 3:
                title = parts[0].strip()
                desc = parts[2].strip()
                if len(desc) > 10: 
                    parsed.append({"course": title, "text": desc})
        return parsed

    # 2. Code Pattern Check (Fallback)
    print("DEBUG: Checking for Course Codes.")
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
            with open("pending_audit.txt", "w") as f: f.write("")
        else:
            print("❌ Error: pending_audit.txt is empty.")
            return

    if not results:
        print("❌ No courses found.")
        return

    print(f"🧠 Auditing {len(results)} courses using Rubin & Dierdorff Framework...")
    print("⏳ Pacing requests for API safety...")
    
    audited = []
    
    # Audit loop
    for item in results[:40]: # Safety limit
        try:
            # --- THE NEW PROMPT ---
            prompt = f"""
            Role: Expert MBA Curriculum Auditor using the Rubin & Dierdorff Competency Model.
            
            Task: Score the following course based on its DESCRIPTION.
            Course: {item['course']}
            Description: {item['text'][:1500]}
            
            Scoring Framework (Depth of Learning):
            0 = Not covered / Irrelevant.
            1 = Theory (Lectures, readings, exams).
            3 = Practice (Case studies, simulations, hypothetical exercises).
            5 = Application (Real-world client projects, fieldwork, creating actual products/companies).
            
            Categories (Based on Rubin & Dierdorff):
            1. Decision_Making: (Stats, Quant, Analytics, Decision Models).
            2. Human_Capital: (OB, Leadership, Negotiation, HR, Teamwork).
            3. Strategy_Innovation: (Corporate Strategy, Competitive Analysis, Entrepreneurship).
            4. Task_Environment: (Marketing, Economics, Global Biz, Policy).
            5. Admin_Control: (Accounting, Finance, Business Law, Compliance).
            6. Logistics_Tech: (Ops Management, Supply Chain, MIS, Tech).

            Return ONLY a flat JSON object:
            {{"Decision_Making": X, "Human_Capital": X, "Strategy_Innovation": X, "Task_Environment": X, "Admin_Control": X, "Logistics_Tech": X}}
            """
            
            res = model.generate_content(prompt)
            clean = res.text.strip().replace("```json","").replace("```","")
            skills = json.loads(clean)
            
            audited.append({"course": item['course'], "skills": skills})
            print(f"   OK: {item['course'][:30]}...")
            
            time.sleep(15) # Maintain safety buffer for 2.5-flash
            
        except Exception as e:
            print(f"   FAIL: {item['course'][:30]}... {e}")
            time.sleep(10)
            continue

    filename = f"{args.name.lower().replace(' ', '_')}_audit.json"
    if audited:
        with open(filename, "w") as f: json.dump(audited, f, indent=2)
        print(f"✅ Created {filename}")
    else:
        print("❌ Audit finished with 0 results.")

if __name__ == "__main__":
    asyncio.run(main())
