import asyncio
import json
import os
import re
import time
import argparse
from openai import OpenAI

# --- SETUP ---
# We now look for the OpenAI Key
api_key = os.environ.get("OPENAI_API_KEY")
client = None

if api_key: 
    client = OpenAI(api_key=api_key)
else:
    print("⚠️ WARNING: No OPENAI_API_KEY found. AI features will fail.")

# The "Fast & Cheap" Model
MODEL_NAME = "gpt-4o-mini"

def parse_text_dump(text):
    """
    Smart Parser V4: Handles Tabs/Spaces or Course Codes.
    (This logic remains unchanged from your original script)
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

def audit_course_openai(course_title, course_desc):
    """
    Sends the course to GPT-4o-Mini for scoring.
    """
    if not client:
        return None

    prompt = f"""
    Task: Score this MBA course using the Rubin & Dierdorff Competency Model.
    
    Course: {course_title}
    Description: {course_desc}
    
    Scoring Scale (Depth of Learning):
    0 = Irrelevant / Not covered.
    1 = Theory (Lectures, readings, exams).
    3 = Practice (Case studies, simulations).
    5 = Application (Real-world projects, consulting, creation).
    
    Categories:
    1. Decision_Making (Data, Analytics, Strategy)
    2. Human_Capital (HR, Leadership, Teams)
    3. Strategy_Innovation (Entrepreneurship, Comp Advantage)
    4. Task_Environment (Marketing, Economics, Policy)
    5. Admin_Control (Accounting, Finance, Law)
    6. Logistics_Tech (Ops, Supply Chain, IT)

    Return JSON ONLY: {{"Decision_Making": 1, "Human_Capital": 0, ...}}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a curriculum auditor. You output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}, # Forces clean JSON
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"    ⚠️ OpenAI Error: {e}")
        return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["url", "text"], required=True)
    parser.add_argument("--input", help="URL or raw text")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    results = []
    
    # Text Mode Logic
    if args.mode == "text":
        if os.path.exists("pending_audit.txt"):
            with open("pending_audit.txt", "r", encoding="utf-8") as f:
                data = f.read()
            results = parse_text_dump(data)
            # Clear file after reading
            with open("pending_audit.txt", "w") as f: f.write("")
        else:
            print("❌ Error: pending_audit.txt is empty.")
            return

    if not results:
        print("❌ No courses found to audit.")
        return

    print(f"🧠 Auditing {len(results)} courses using OpenAI ({MODEL_NAME})...")
    
    audited = []
    
    # Audit loop
    for i, item in enumerate(results[:50]): # Safety limit raised to 50
        print(f"   Processing [{i+1}/{len(results)}]: {item['course'][:30]}...")
        
        skills = audit_course_openai(item['course'], item['text'][:1500])
        
        if skills:
            audited.append({"course": item['course'], "skills": skills})
            print(f"     ✅ Scored.")
        else:
            print(f"     ❌ Failed.")

        # OpenAI is faster, 1 second sleep is usually enough
        time.sleep(1)

    # Save Results
    filename = f"{args.name.lower().replace(' ', '_')}_audit.json"
    if audited:
        with open(filename, "w") as f: json.dump(audited, f, indent=2)
        print(f"✅ Created {filename}")
    else:
        print("❌ Audit finished with 0 results.")

if __name__ == "__main__":
    asyncio.run(main())
