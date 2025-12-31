import asyncio
import json
import os
import re
import time
import sys
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- SETUP ---
genai.configure(api_key=os.environ.get("AIzaSyC_fQtJV9MD4RFikgQGga4CRWZJrAkaFEg"))
model = genai.GenerativeModel('gemini-pro')

async def run_audit(url, school_name):
    print(f"🕵️ Deep Auditing: {school_name}...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Change to False to debug locally
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url)
            await asyncio.sleep(5)

            # --- SCHOOL SPECIFIC "WAKE UP" ACTIONS ---
            if "nyu.edu" in url:
                print("🗽 Triggering NYU Stern List...")
                # Stern often needs a click on 'Course Index' or 'View All'
                await page.get_by_text("Course Index", exact=False).first.click()
            
            if "kellogg.northwestern.edu" in url:
                print("🟣 Triggering Kellogg Search...")
                # Kellogg needs you to hit 'Search' on an empty box to see all
                await page.get_by_role("button", name="Search").click()

            await asyncio.sleep(5) # Wait for results to populate

            # --- THE RESET LOOP ---
            # We look for course codes (e.g., MGMT-GB.2314 or ACCT-430)
            pattern = re.compile(r"[A-Z]{2,4}[-\s]\d{3,4}")
            
            for i in range(30): # Start with 30 to test
                print(f"🔄 Finding targets (Attempt {i+1})...")
                all_matches = await page.get_by_text(pattern).all()
                
                # Filter out garbage
                valid = [el for el in all_matches if len(await el.text_content()) < 100]
                
                if i >= len(valid): break

                target = valid[i]
                title = (await target.text_content()).strip()
                await target.scroll_into_view_if_needed()

                print(f"🚀 Opening: {title}...")
                try:
                    async with page.expect_popup(timeout=8000) as popup_info:
                        await target.click()
                    
                    new_tab = await popup_info.value
                    await new_tab.wait_for_load_state()
                    clean_text = await new_tab.inner_text("body")
                    
                    if len(clean_text) > 100:
                        results.append({"course": title, "text": clean_text})
                    
                    await new_tab.close()
                except:
                    print(f"⚠️ Skip {i}: No tab opened.")
                    continue

        except Exception as e:
            print(f"❌ Critical Error: {e}")

        await browser.close()

    # --- GEMINI-PRO AUDIT ---
    if not results:
        print("❌ Final Result: 0 courses found. Loop failed.")
        return

    print(f"🧠 Auditing {len(results)} courses...")
    audited = []
    for item in results:
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
    
    # Update Registry
    update_registry(school_id, school_name, filename)
    print(f"✅ SUCCESS! Created {filename}")

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
    asyncio.run(run_audit(sys.argv[1], sys.argv[2]))

