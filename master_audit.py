import asyncio
import json
import os
import re
import time
import sys
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- SETUP ---
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

async def run_audit(url, school_name):
    print(f"🕵️ Deep Auditing: {school_name}...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. Navigate
            await page.goto(url, wait_until="domcontentloaded")
            
            # --- NYU STERN / KELLOGG TRIGGER ---
            if "nyu.edu" in url:
                print("🗽 Clicking 'Course Index'...")
                # We use a broad text search to find the trigger button
                trigger = page.get_by_text("Course Index", exact=False).first
                if await trigger.is_visible():
                    await trigger.click()
            
            if "kellogg.northwestern.edu" in url:
                print("🟣 Clicking Kellogg 'Search'...")
                await page.get_by_role("button", name="Search").click()

            # --- THE PATIENCE LOOP (The Fix) ---
            print("⏳ Waiting for courses to lazy-load...")
            pattern = re.compile(r"[A-Z]{2,4}[-\s\.][A-Z]{0,2}\d{3,4}")
            
            found_data = False
            for attempt in range(20): # Wait up to 20 seconds
                # Search all frames for the course pattern
                for frame in page.frames:
                    try:
                        matches = await frame.get_by_text(pattern).all()
                        if len(matches) > 0:
                            print(f"✅ Courses appeared after {attempt}s!")
                            found_data = True
                            break
                    except: continue
                if found_data: break
                await asyncio.sleep(1)

            if not found_data:
                print("❌ ERROR: Courses never appeared on screen.")
                await browser.close()
                return

            # --- THE RESET LOOP ---
            for i in range(35):
                valid_elements = []
                for frame in page.frames:
                    try:
                        matches = await frame.get_by_text(pattern).all()
                        for m in matches:
                            text = await m.text_content()
                            if text and len(text.strip()) < 100:
                                valid_elements.append((frame, m))
                    except: continue

                if i >= len(valid_elements): break

                current_frame, target_el = valid_elements[i]
                title = (await target_el.text_content()).strip()
                
                # Deduplicate
                if any(r['course'] == title for r in results): continue

                print(f"🚀 [{len(results)+1}] Opening: {title}...")
                
                try:
                    await target_el.scroll_into_view_if_needed()
                    async with page.expect_popup(timeout=10000) as popup_info:
                        await target_el.click()
                    
                    new_tab = await popup_info.value
                    await new_tab.wait_for_load_state()
                    clean_text = await new_tab.inner_text("body")
                    
                    if len(clean_text) > 150:
                        results.append({"course": title, "text": clean_text})
                    
                    await new_tab.close()
                except: continue

        except Exception as e:
            print(f"❌ Critical Error: {e}")
        finally:
            await browser.close()

    # --- GEMINI-PRO AUDIT ---
    if not results:
        ensure_registry_exists()
        return

    print(f"🧠 Auditing {len(results)} courses...")
    audited = []
    for item in results:
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
